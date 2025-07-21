from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/")
def create_user():
    return {"message": "User creation stub"}
