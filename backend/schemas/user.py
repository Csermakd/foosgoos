from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)

    player1_matches = relationship("Match", foreign_keys='Match.player1_id')
    player2_matches = relationship("Match", foreign_keys='Match.player2_id')
    player3_matches = relationship("Match", foreign_keys='Match.player3_id')
    player4_matches = relationship("Match", foreign_keys='Match.player4_id')

    stats = relationship("PlayerStats", back_populates="player", uselist=False, cascade="all, delete-orphan")
