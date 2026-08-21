from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime,
    Enum as SqlEnum,
)
from sqlalchemy.orm import relationship
from database import Base
from enums.team import TeamEnum
from enums.goal_event import GoalSourceEnum, GoalStatusEnum, GoalBarEnum
import datetime


def _values(enum_cls):
    """Store the lowercase enum *value* in SQLite, not the python member
    name, so the DB is readable and matches the JSON on the wire."""
    return [e.value for e in enum_cls]


class GoalEvent(Base):
    """One goal, durably stored the moment it happens.

    Before this existed, goals lived only in React useState and were lost
    on refresh. Everything downstream depends on them being persisted:
    live score, undo, per-player stats, and - crucially - the ground-truth
    log we evaluate the vision model against.
    """
    __tablename__ = "goal_events"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, index=True)

    # Idempotency key. The vision service generates this and retries with
    # the SAME uuid, so a flaky network cannot score the same goal twice.
    event_uuid = Column(String, unique=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Milliseconds since the match recording started. This is what lets us
    # line an event up with a frame in the recorded video later.
    video_ts_ms = Column(Integer, nullable=True)

    # The team that gets the point (for an own goal, that is the OPPOSING
    # team - see own_goal below).
    team = Column(
        SqlEnum(TeamEnum, values_callable=_values), nullable=False
    )

    # Who it is attributed to. NULL is legal and expected: the camera can
    # see a goal without knowing which human is responsible.
    player_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    bar = Column(
        SqlEnum(GoalBarEnum, values_callable=_values),
        default=GoalBarEnum.UNKNOWN, nullable=False,
    )
    own_goal = Column(Boolean, default=False, nullable=False)

    source = Column(
        SqlEnum(GoalSourceEnum, values_callable=_values),
        default=GoalSourceEnum.MANUAL, nullable=False,
    )
    status = Column(
        SqlEnum(GoalStatusEnum, values_callable=_values),
        default=GoalStatusEnum.CONFIRMED, nullable=False,
    )
    confidence = Column(Float, nullable=True)   # camera events only

    # Free-text note on how the detection fired ("line_crossing",
    # "disappearance") - useful when debugging false positives later.
    detector_note = Column(String, nullable=True)

    match = relationship("Match", back_populates="goal_events")

    @property
    def counts_for_score(self) -> bool:
        return self.status != GoalStatusEnum.REJECTED
