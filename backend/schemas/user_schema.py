from pydantic import BaseModel
from typing import Optional
from schemas.player_stats_schema import PlayerStats

class UserBase(BaseModel):
    name: str
    # email: Optional[str] = None

class UserCreate(UserBase):
    # hashed_password: Optional[str] = None
    pass

class User(UserBase):
    id: int
    stats: Optional[PlayerStats] = None

    class Config:
        from_attributes = True