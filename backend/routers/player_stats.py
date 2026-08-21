from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import User as UserModel
from models.player_stats import PlayerStats as PlayerStatsModel
from schemas.player_stats_schema import PlayerStats
from database import get_db

router = APIRouter(prefix="/stats", tags=["Player Stats"])


@router.get("/users", response_model=PlayerStats)
def get_player_stats(username: str, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.name == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    stats = db.query(PlayerStatsModel).filter(PlayerStatsModel.user_id == db_user.id).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Player stats not found")

    return stats
