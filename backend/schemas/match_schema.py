from pydantic import BaseModel, ConfigDict
from enums.winning_team import WinningTeamEnum
from enums.match_status import MatchStatusEnum
from datetime import datetime
from typing import List, Optional
from schemas.player_stats_schema import PlayerStatsCreate
from schemas.goal_event_schema import GoalEvent


class MatchBase(BaseModel):
    player1_id: int   # blue offense
    player2_id: int   # blue defense
    player3_id: int   # red offense
    player4_id: int   # red defense


class MatchStart(MatchBase):
    """POST /matches/start - called the moment the four players are
    chosen, before a single point is played."""
    pass


class MatchCreate(MatchBase):
    """Legacy one-shot create: the whole finished match in a single POST.
    Kept so old clients keep working; new clients should use
    /matches/start + /matches/{id}/events + /matches/{id}/finish."""
    winner_team: WinningTeamEnum = WinningTeamEnum.NONE
    score_blue: int = 0
    score_red: int = 0
    player_stats: List[PlayerStatsCreate] = []


class Match(MatchBase):
    id: int
    timestamp: datetime
    winner_team: WinningTeamEnum
    score_blue: int
    score_red: int
    status: MatchStatusEnum
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    video_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MatchDetail(Match):
    """A match plus its full goal log - what GamePlay loads on refresh so
    an in-progress game survives a browser reload."""
    goal_events: List[GoalEvent] = []


class MatchFinish(BaseModel):
    """Optional overrides at finish time. Normally empty: the final score
    is derived from the goal_events log, not sent by the client."""
    abandoned: bool = False


class VideoPathUpdate(BaseModel):
    """The vision service reports where it saved this match's recording."""
    video_path: str
