from pydantic import BaseModel

class PlayerStatsBase(BaseModel):
    user_id: int
    goals: int = 0
    goals_from_offense: int = 0
    goals_from_defense: int = 0
    saves: int = 0

class PlayerStatsCreate(PlayerStatsBase):
    pass

class PlayerStats(PlayerStatsBase):
    id: int

    class Config:
        orm_mode = True