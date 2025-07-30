from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Player Stats"])

@router.get("/")
def get_player_stats():
    return {"message": "Get requested player's stats"}
