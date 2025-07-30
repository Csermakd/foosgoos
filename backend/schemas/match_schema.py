from pydantic import BaseModel
from enums.winning_team import WinningTeamEnum
from datetime import datetime

class MatchBase(BaseModel):
    player1_id: int
    player2_id: int
    player3_id: int
    player4_id: int
    winner_team: WinningTeamEnum

class MatchCreate(MatchBase):
    pass

class Match(MatchBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True