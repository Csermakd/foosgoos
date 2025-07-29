from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SqlEnum
from database import Base
from enums.winning_team import WinningTeamEnum
import datetime

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    player1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player3_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player4_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    winner_team = Column(SqlEnum(WinningTeamEnum), default=WinningTeamEnum.NONE)  
