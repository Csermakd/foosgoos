from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/")
def create_user():
    return {"message": "User creation stub"}

@router.get("/")
def get_user():
    return {"message": "Get requested User"}
