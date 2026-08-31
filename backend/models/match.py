from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SqlEnum
from sqlalchemy.orm import relationship
from database import Base
from enums.winning_team import WinningTeamEnum
from enums.match_status import MatchStatusEnum
import datetime


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # blue offense
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # blue defense
    player3_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # red offense
    player4_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # red defense

    score_blue = Column(Integer, default=0)
    score_red = Column(Integer, default=0)

    winner_team = Column(SqlEnum(WinningTeamEnum), default=WinningTeamEnum.NONE)

    # --- match lifecycle (added for assisted/camera mode) ---
    # A match row now exists for the whole duration of the game so goal
    # events and a video recording have something to attach to.
    status = Column(
        SqlEnum(MatchStatusEnum, values_callable=lambda x: [e.value for e in x]),
        default=MatchStatusEnum.IN_PROGRESS, nullable=False, index=True,
    )
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Path (on the camera machine) of the video recorded for this match.
    # Recorded footage + the goal_events log = our labelled dataset.
    video_path = Column(String, nullable=True)

    goal_events = relationship(
        "GoalEvent", back_populates="match",
        cascade="all, delete-orphan", order_by="GoalEvent.id",
    )
