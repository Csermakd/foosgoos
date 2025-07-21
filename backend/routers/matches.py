from fastapi import APIRouter

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.post("/")
def create_match():
    return {"message": "Match creation stub"}
