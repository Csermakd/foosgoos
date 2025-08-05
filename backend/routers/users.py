from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.user_schema import UserCreate, User
from models.user import User as UserModel
from database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
def get_user(username: str, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.name == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

 
@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.name == user.name).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    db_user = UserModel(
        name=user.name, 
        email=user.email, 
        hashed_password=user.hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
