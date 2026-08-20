from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from models.match import Match as MatchModel
from models.goal_event import GoalEvent as GoalEventModel
from models.player_stats import PlayerStats as PlayerStatsModel
from schemas.match_schema import (
    MatchCreate, MatchStart, MatchFinish, Match, MatchDetail, VideoPathUpdate,
)
from schemas.goal_event_schema import (
    GoalEventCreate, GoalEventUpdate, GoalEvent, GoalEventResult, Score,
)
from enums.winning_team import WinningTeamEnum
from enums.match_status import MatchStatusEnum
from enums.team import TeamEnum
from enums.goal_event import GoalSourceEnum, GoalStatusEnum, GoalBarEnum
from database import get_db
from realtime import manager

router = APIRouter(prefix="/matches", tags=["Matches"])

OFFENSE_BARS = {GoalBarEnum.FIVE_BAR, GoalBarEnum.THREE_BAR}
DEFENSE_BARS = {GoalBarEnum.TWO_BAR, GoalBarEnum.GOALIE}


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------

def _get_match_or_404(db: Session, match_id: int) -> MatchModel:
    match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    return match


def _scoring_events(match: MatchModel) -> List[GoalEventModel]:
    return [e for e in match.goal_events if e.status != GoalStatusEnum.REJECTED]


def _recompute_score(match: MatchModel) -> Score:
    """The score is always DERIVED from the goal log, never incremented in
    place. That makes undo, correction and out-of-order arrival trivially
    correct - there is no running counter to get out of step."""
    blue = sum(1 for e in _scoring_events(match) if e.team == TeamEnum.BLUE)
    red = sum(1 for e in _scoring_events(match) if e.team == TeamEnum.RED)
    match.score_blue = blue
    match.score_red = red
    return Score(blue=blue, red=red)


def _team_of_player(match: MatchModel, player_id: Optional[int]) -> Optional[TeamEnum]:
    if player_id is None:
        return None
    if player_id in (match.player1_id, match.player2_id):
        return TeamEnum.BLUE
    if player_id in (match.player3_id, match.player4_id):
        return TeamEnum.RED
    return None


def _result_payload(event: GoalEventModel, score: Score, duplicate: bool = False) -> dict:
    return GoalEventResult(
        event=GoalEvent.model_validate(event), score=score, duplicate=duplicate,
    ).model_dump(mode="json")


async def _broadcast(match_id: int, kind: str, payload: dict):
    await manager.broadcast(match_id, {"type": kind, **payload})


def _get_or_create_stats(db: Session, user_id: int) -> PlayerStatsModel:
    stats = db.query(PlayerStatsModel).filter(
        PlayerStatsModel.user_id == user_id
    ).first()
    if stats is None:
        stats = PlayerStatsModel(
            user_id=user_id, goals=0, goals_from_offense=0,
            goals_from_defense=0, own_goals=0, saves=0,
            matches_played=0, matches_won=0,
        )
        db.add(stats)
        # The session is autoflush=False, so without this an immediately
        # following lookup for the same user would miss the pending row
        # and insert a second one - which SQLite then rejects on the
        # unique constraint at commit time.
        db.flush()
    return stats


# ------------------------------------------------------------------
# match lifecycle
# ------------------------------------------------------------------

@router.post("/start", response_model=Match)
def start_match(payload: MatchStart, db: Session = Depends(get_db)):
    """Create the match row when the players are picked.

    Everything else in assisted mode hangs off the id this returns: the
    goal log, the websocket room, and the video file the vision service
    records.
    """
    existing = db.query(MatchModel).filter(
        MatchModel.status == MatchStatusEnum.IN_PROGRESS
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Match {existing.id} is still in progress. Finish or abandon "
                f"it before starting a new one."
            ),
        )

    ids = [payload.player1_id, payload.player2_id, payload.player3_id, payload.player4_id]
    if len(set(ids)) != 4:
        raise HTTPException(status_code=400, detail="The same player was picked twice")

    now = datetime.utcnow()
    match = MatchModel(
        player1_id=payload.player1_id,
        player2_id=payload.player2_id,
        player3_id=payload.player3_id,
        player4_id=payload.player4_id,
        status=MatchStatusEnum.IN_PROGRESS,
        winner_team=WinningTeamEnum.NONE,
        score_blue=0, score_red=0,
        timestamp=now, started_at=now,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/active", response_model=Optional[MatchDetail])
def get_active_match(db: Session = Depends(get_db)):
    """The single in-progress match, or null.

    The vision service polls this instead of the backend pushing to it -
    that way the camera machine can reboot, reconnect, or be started
    mid-game and it will just pick up wherever things are. No service
    discovery, no held connection to get stale.
    """
    return db.query(MatchModel).filter(
        MatchModel.status == MatchStatusEnum.IN_PROGRESS
    ).order_by(MatchModel.id.desc()).first()


@router.post("/{match_id}/finish", response_model=MatchDetail)
async def finish_match(match_id: int, payload: MatchFinish = MatchFinish(),
                       db: Session = Depends(get_db)):
    """Close the match: derive the final score from the goal log, decide a
    winner, and roll the per-player stats up exactly once."""
    match = _get_match_or_404(db, match_id)
    if match.status != MatchStatusEnum.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail=f"Match {match_id} is already {match.status.value}",
        )

    if payload.abandoned:
        match.status = MatchStatusEnum.ABANDONED
        match.ended_at = datetime.utcnow()
        _recompute_score(match)
        db.commit()
        db.refresh(match)
        await _broadcast(match_id, "match_finished",
                         {"match_id": match_id, "status": match.status.value})
        return match

    score = _recompute_score(match)
    if score.blue > score.red:
        match.winner_team = WinningTeamEnum.TEAM_BLUE
    elif score.red > score.blue:
        match.winner_team = WinningTeamEnum.TEAM_RED
    else:
        match.winner_team = WinningTeamEnum.NONE

    _rollup_player_stats(db, match)

    match.status = MatchStatusEnum.COMPLETED
    match.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(match)

    await _broadcast(match_id, "match_finished", {
        "match_id": match_id,
        "status": match.status.value,
        "score": score.model_dump(),
        "winner_team": match.winner_team.value,
    })
    return match


def _rollup_player_stats(db: Session, match: MatchModel):
    """Fold this match's goal log into the lifetime PlayerStats rows.

    Events with player_id = NULL (camera saw the goal, nobody said who
    scored it) still count towards the team score but deliberately do not
    inflate anyone's personal numbers.
    """
    roster = [match.player1_id, match.player2_id, match.player3_id, match.player4_id]
    winner_ids = []
    if match.winner_team == WinningTeamEnum.TEAM_BLUE:
        winner_ids = [match.player1_id, match.player2_id]
    elif match.winner_team == WinningTeamEnum.TEAM_RED:
        winner_ids = [match.player3_id, match.player4_id]

    for user_id in roster:
        stats = _get_or_create_stats(db, user_id)
        stats.matches_played = (stats.matches_played or 0) + 1
        if user_id in winner_ids:
            stats.matches_won = (stats.matches_won or 0) + 1

    for event in _scoring_events(match):
        if event.player_id is None:
            continue
        stats = _get_or_create_stats(db, event.player_id)
        if event.own_goal:
            stats.own_goals = (stats.own_goals or 0) + 1
            continue
        stats.goals = (stats.goals or 0) + 1
        if event.bar in OFFENSE_BARS:
            stats.goals_from_offense = (stats.goals_from_offense or 0) + 1
        elif event.bar in DEFENSE_BARS:
            stats.goals_from_defense = (stats.goals_from_defense or 0) + 1
        # bar == UNKNOWN counts towards total goals but towards neither
        # offense nor defense - we genuinely do not know which it was.


@router.post("/{match_id}/video", response_model=Match)
def set_video_path(match_id: int, payload: VideoPathUpdate,
                   db: Session = Depends(get_db)):
    """The vision service reports where it wrote this match's recording,
    so we can find the footage for a given game months from now."""
    match = _get_match_or_404(db, match_id)
    match.video_path = payload.video_path
    db.commit()
    db.refresh(match)
    return match


# ------------------------------------------------------------------
# goal events
# ------------------------------------------------------------------

@router.post("/{match_id}/events", response_model=GoalEventResult)
async def add_goal_event(match_id: int, payload: GoalEventCreate,
                         db: Session = Depends(get_db)):
    """Record a goal. Called by the app when a human taps a button, and by
    the vision service when it detects one.

    Idempotent on event_uuid: retrying a request that already landed
    returns the stored event with duplicate=true instead of scoring twice.
    """
    match = _get_match_or_404(db, match_id)

    existing = db.query(GoalEventModel).filter(
        GoalEventModel.event_uuid == payload.event_uuid
    ).first()
    if existing:
        return _result_payload(existing, _recompute_score(match), duplicate=True)

    if match.status != MatchStatusEnum.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail=f"Match {match_id} is {match.status.value}; it accepts no new goals",
        )

    if payload.player_id is not None:
        if _team_of_player(match, payload.player_id) is None:
            raise HTTPException(
                status_code=400,
                detail=f"Player {payload.player_id} is not in match {match_id}",
            )

    # Camera events start life needing a human glance; manual taps are
    # confirmed by definition - a human just made them.
    status = payload.status
    if status is None:
        status = (GoalStatusEnum.PENDING_REVIEW
                  if payload.source == GoalSourceEnum.CAMERA
                  else GoalStatusEnum.CONFIRMED)

    event = GoalEventModel(
        match_id=match_id,
        event_uuid=payload.event_uuid,
        team=payload.team,
        player_id=payload.player_id,
        bar=payload.bar,
        own_goal=payload.own_goal,
        source=payload.source,
        status=status,
        confidence=payload.confidence,
        video_ts_ms=payload.video_ts_ms,
        detector_note=payload.detector_note,
    )
    db.add(event)
    db.flush()          # populate event.id before we recompute
    db.refresh(match)
    score = _recompute_score(match)
    db.commit()
    db.refresh(event)

    payload_out = _result_payload(event, score)
    await _broadcast(match_id, "goal_added", payload_out)
    return payload_out


@router.get("/{match_id}/events", response_model=List[GoalEvent])
def list_goal_events(match_id: int, db: Session = Depends(get_db)):
    match = _get_match_or_404(db, match_id)
    return match.goal_events


@router.patch("/{match_id}/events/{event_id}", response_model=GoalEventResult)
async def update_goal_event(match_id: int, event_id: int, payload: GoalEventUpdate,
                            db: Session = Depends(get_db)):
    """The human half of assisted mode: confirm, correct, or reject what
    the camera proposed. Rejecting is what makes the score drop back."""
    match = _get_match_or_404(db, match_id)
    event = db.query(GoalEventModel).filter(
        GoalEventModel.id == event_id,
        GoalEventModel.match_id == match_id,
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Goal event {event_id} not found")

    fields = payload.model_dump(exclude_unset=True)
    if "player_id" in fields and fields["player_id"] is not None:
        if _team_of_player(match, fields["player_id"]) is None:
            raise HTTPException(
                status_code=400,
                detail=f"Player {fields['player_id']} is not in match {match_id}",
            )
    for key, value in fields.items():
        setattr(event, key, value)

    # Any human edit implies a human has now looked at it.
    if fields and "status" not in fields and event.status == GoalStatusEnum.PENDING_REVIEW:
        event.status = GoalStatusEnum.CONFIRMED

    db.flush()
    db.refresh(match)
    score = _recompute_score(match)
    db.commit()
    db.refresh(event)

    payload_out = _result_payload(event, score)
    await _broadcast(match_id, "goal_updated", payload_out)
    return payload_out


@router.delete("/{match_id}/events/{event_id}", response_model=Score)
async def delete_goal_event(match_id: int, event_id: int, db: Session = Depends(get_db)):
    """Hard delete - the Rewind button. Use PATCH status=rejected instead
    when you want to keep the record that the camera got it wrong, which
    is the more useful signal for improving the model."""
    match = _get_match_or_404(db, match_id)
    event = db.query(GoalEventModel).filter(
        GoalEventModel.id == event_id,
        GoalEventModel.match_id == match_id,
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Goal event {event_id} not found")

    db.delete(event)
    db.flush()
    db.refresh(match)
    score = _recompute_score(match)
    db.commit()

    await _broadcast(match_id, "goal_deleted",
                     {"event_id": event_id, "score": score.model_dump()})
    return score


# ------------------------------------------------------------------
# reads
# ------------------------------------------------------------------

@router.get("/", response_model=List[Match])
def get_matches(
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
    status: Optional[MatchStatusEnum] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List matches, newest first, optionally filtered.

    (There used to be a second @router.get("/") below this one holding the
    id/time-range filters. FastAPI matches the first registration, so that
    handler was unreachable dead code - its behaviour is folded in here
    and into GET /matches/{match_id}.)
    """
    query = db.query(MatchModel)
    if starttime is not None:
        query = query.filter(MatchModel.timestamp >= starttime)
    if endtime is not None:
        query = query.filter(MatchModel.timestamp <= endtime)
    if status is not None:
        query = query.filter(MatchModel.status == status)
    return query.order_by(MatchModel.timestamp.desc()).limit(limit).all()


@router.get("/{match_id}", response_model=MatchDetail)
def get_match(match_id: int, db: Session = Depends(get_db)):
    """A match with its full goal log. GamePlay calls this on mount so a
    browser refresh mid-game restores the exact state."""
    return _get_match_or_404(db, match_id)


# ------------------------------------------------------------------
# legacy
# ------------------------------------------------------------------

@router.post("/", response_model=Match, deprecated=True)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    """Legacy: post an entire finished match in one shot.

    Superseded by start -> events -> finish. Kept working so nothing that
    still points at it breaks, but it writes no goal_events, so matches
    created this way have no reviewable goal log and no video alignment.
    """
    now = datetime.utcnow()
    db_match = MatchModel(
        player1_id=match.player1_id,
        player2_id=match.player2_id,
        player3_id=match.player3_id,
        player4_id=match.player4_id,
        winner_team=match.winner_team,
        score_blue=match.score_blue,
        score_red=match.score_red,
        status=MatchStatusEnum.COMPLETED,
        timestamp=now, started_at=now, ended_at=now,
    )
    db.add(db_match)

    for stat in match.player_stats:
        db_stat = _get_or_create_stats(db, stat.user_id)
        db_stat.goals = (db_stat.goals or 0) + stat.goals
        db_stat.goals_from_offense = (db_stat.goals_from_offense or 0) + stat.goals_from_offense
        db_stat.goals_from_defense = (db_stat.goals_from_defense or 0) + stat.goals_from_defense
        db_stat.saves = (db_stat.saves or 0) + stat.saves

    db.commit()
    db.refresh(db_match)
    return db_match


# ------------------------------------------------------------------
# websocket
# ------------------------------------------------------------------

@router.websocket("/ws/{match_id}")
async def match_socket(websocket: WebSocket, match_id: int):
    """Live feed of goal events for one match.

    Clients should treat this as a hint to update, not as the source of
    truth - every message carries the full derived score, and a client
    that reconnects re-syncs with GET /matches/{id}.
    """
    await manager.connect(match_id, websocket)
    try:
        while True:
            # We never expect inbound messages; this just keeps the socket
            # open and notices the client going away.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(match_id, websocket)
