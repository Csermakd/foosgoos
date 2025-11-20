from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from schemas.user_schema import UserCreate, User
from models.user import User as UserModel
from database import get_db
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=User)
def get_user(username: str, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.name == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

 
@router.post("/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.name == user.name).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    db_user = UserModel(
        name=user.name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# need to fetch the list of all users (with their IDs) before the game starts,
# in CreateGame.tsx. Then pass those IDs to the Redux state,
# so GamePlay.tsx can use them when the match is over

@router.get("/all", response_model=List[User])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserModel).options(joinedload(UserModel.stats)).all()
    return users 
