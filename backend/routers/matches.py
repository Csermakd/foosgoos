from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.match import Match as MatchModel
from schemas.match_schema import MatchCreate, Match
from database import get_db
from typing import List
from datetime import datetime

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.post("/")
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    db_match = MatchModel(
        player1_id=match.player1_id,
        player2_id=match.player2_id,
        player3_id=match.player3_id,
        player4_id=match.player4_id,
        winner_team=match.winner_team
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


@router.get("/")
def get_match(match_id: int, starttime: Optional[datetime] = None, endtime: Optional[datetime] = None, db: Session = Depends(get_db)):
    match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

    # case 2: query by given time range
    elif starttime is not None and endtime is not None:
        matches = db.query(MatchModel).filter(MatchModel.timestamp >= starttime, MatchModel.timestamp <= endtime).all()
        # returns empty list if no matches found
        return matches

    # no valid parameters ig
    else:
        raise HTTPException(status_code=400, detail="missing 'match_id' OR both 'starttime' and 'endtime'.")
