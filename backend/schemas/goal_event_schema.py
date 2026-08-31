from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
import uuid

from enums.team import TeamEnum
from enums.goal_event import GoalSourceEnum, GoalStatusEnum, GoalBarEnum


class GoalEventCreate(BaseModel):
    """Body for POST /matches/{id}/events.

    Only `team` is required. Everything else is optional because the two
    producers know different things: a human tapping a button knows the
    player and the bar; the camera knows the team and the timestamp and
    usually nothing else.
    """
    team: TeamEnum
    event_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: Optional[int] = None
    bar: GoalBarEnum = GoalBarEnum.UNKNOWN
    own_goal: bool = False
    source: GoalSourceEnum = GoalSourceEnum.MANUAL
    status: Optional[GoalStatusEnum] = None   # defaulted by source if omitted
    confidence: Optional[float] = None
    video_ts_ms: Optional[int] = None
    detector_note: Optional[str] = None


class GoalEventUpdate(BaseModel):
    """Body for PATCH - the human correcting or confirming the camera."""
    team: Optional[TeamEnum] = None
    player_id: Optional[int] = None
    bar: Optional[GoalBarEnum] = None
    own_goal: Optional[bool] = None
    status: Optional[GoalStatusEnum] = None


class GoalEvent(BaseModel):
    id: int
    match_id: int
    event_uuid: str
    created_at: datetime
    video_ts_ms: Optional[int] = None
    team: TeamEnum
    player_id: Optional[int] = None
    bar: GoalBarEnum
    own_goal: bool
    source: GoalSourceEnum
    status: GoalStatusEnum
    confidence: Optional[float] = None
    detector_note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Score(BaseModel):
    blue: int
    red: int


class GoalEventResult(BaseModel):
    """What both the HTTP response and the websocket broadcast carry:
    the event plus the resulting score, so no client ever has to
    recompute the score itself and drift out of sync."""
    event: GoalEvent
    score: Score
    duplicate: bool = False   # true if this event_uuid was already stored
