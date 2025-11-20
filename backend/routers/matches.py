from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.match import Match as MatchModel
from models.player_stats import PlayerStats as PlayerStatsModel
from schemas.match_schema import MatchCreate, Match
from database import get_db
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.post("/", response_model=Match)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    # 1. Create the Match Record
    db_match = MatchModel(
        player1_id=match.player1_id,
        player2_id=match.player2_id,
        player3_id=match.player3_id,
        player4_id=match.player4_id,
        winner_team=match.winner_team,
        score_blue=match.score_blue,
        score_red=match.score_red
    )
    db.add(db_match)
    
    for stat in match.player_stats:
        # Check if stats row exists for this user
        db_stat = db.query(PlayerStatsModel).filter(PlayerStatsModel.user_id == stat.user_id).first()
        
        if not db_stat:
            # Explicitly set all counters to 0 so we can do math on them immediately
            db_stat = PlayerStatsModel(
                user_id=stat.user_id,
                goals=0,
                goals_from_offense=0,
                goals_from_defense=0,
                saves=0
            )
            db.add(db_stat)
        
        db_stat.goals = (db_stat.goals or 0) + stat.goals
        db_stat.goals_from_offense = (db_stat.goals_from_offense or 0) + stat.goals_from_offense
        db_stat.goals_from_defense = (db_stat.goals_from_defense or 0) + stat.goals_from_defense
        db_stat.saves = (db_stat.saves or 0) + stat.saves

    db.commit()
    db.refresh(db_match)
    return db_match

@router.get("/", response_model=List[Match])
def get_matches(db: Session = Depends(get_db)):
    # Return all matches, newest first
    return db.query(MatchModel).order_by(MatchModel.timestamp.desc()).all()


@router.get("/")
def get_match(match_id: Optional[int] = None, starttime: Optional[datetime] = None, endtime: Optional[datetime] = None, db: Session = Depends(get_db)):
    if match_id is not None:
        match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
        if not match:
            # raise HTTPException(status_code=404, detail=f"Match with id {match_id} not found")
            return []
        return [match]

    # case 2: query by given time range
    elif starttime is not None and endtime is not None:
        matches = db.query(MatchModel).filter(MatchModel.timestamp >= starttime, MatchModel.timestamp <= endtime).all()
        # returns empty list if no matches found
        return matches

    # no valid parameters ig
    else:
        raise HTTPException(status_code=400, detail="missing 'match_id' OR both 'starttime' and 'endtime'.")
