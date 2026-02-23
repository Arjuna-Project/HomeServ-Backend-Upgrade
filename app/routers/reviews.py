from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.review import ReviewCreate
from app.utils.dependencies import get_current_user, get_db
from app.models.review import Review
from app.models.user import User

router = APIRouter(prefix="/reviews", tags=["Review"])

@router.post("")
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    review = Review(
        booking_id=data.booking_id,
        rating=data.rating,
        comment=data.comment
    )

    db.add(review)
    db.commit()
    return {"message": "Review submitted"}
