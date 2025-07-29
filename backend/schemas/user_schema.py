from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: Optional[str] = None

class UserCreate(UserBase):
    hashed_password: Optional[str] = None

class User(UserBase):
    id: int

    class Config:
        orm_mode = True