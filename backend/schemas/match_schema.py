from pydantic import BaseModel
from enums.winning_team import WinningTeamEnum
from datetime import datetime
from typing import List
from schemas.player_stats_schema import PlayerStatsCreate

class MatchBase(BaseModel):
    player1_id: int
    player2_id: int
    player3_id: int
    player4_id: int
    winner_team: WinningTeamEnum
    score_blue: int
    score_red: int

class MatchCreate(MatchBase):
    # Allow receiving a list of stats
    player_stats: List[PlayerStatsCreate] = []

class Match(MatchBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True