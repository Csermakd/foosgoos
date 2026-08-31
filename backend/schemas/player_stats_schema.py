from pydantic import BaseModel, ConfigDict


class PlayerStatsBase(BaseModel):
    user_id: int
    goals: int = 0
    goals_from_offense: int = 0
    goals_from_defense: int = 0
    own_goals: int = 0
    saves: int = 0
    matches_played: int = 0
    matches_won: int = 0


class PlayerStatsCreate(PlayerStatsBase):
    pass


class PlayerStats(PlayerStatsBase):
    model_config = ConfigDict(from_attributes=True)
