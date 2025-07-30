from fastapi import APIRouter

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.post("/")
def create_match():
    return {"message": "Match creation stub"}

@router.get("/")
def get_match():
    return {"message": "Get requested Match"}
