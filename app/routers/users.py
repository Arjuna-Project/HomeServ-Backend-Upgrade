from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserProfile
from app.utils.dependencies import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["User"])

@router.get("/me", response_model=UserProfile)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
