from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class PlayerStats(Base):
    __tablename__ = "player_stats"

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, primary_key=True, index=True)

    goals = Column(Integer, default=0)
    goals_from_offense = Column(Integer, default=0)
    goals_from_defense = Column(Integer, default=0)
    saves = Column(Integer, default=0)

    player = relationship("User", back_populates="stats")