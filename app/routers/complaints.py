from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.dependencies import get_current_user, get_db
from app.schemas.complaint import ComplaintCreate, ComplaintResponse
from app.models.complaint import Complaint
from app.models.user import User
from app.models.booking import Booking

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintResponse)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 1️⃣ Check booking belongs to current user
    booking = db.query(Booking).filter(
        Booking.id == data.booking_id,
        Booking.user_id == current_user.id
    ).first()

    if not booking:
        raise HTTPException(status_code=403, detail="Not allowed")

    # 2️⃣ Create complaint
    complaint = Complaint(
        booking_id=data.booking_id,
        description=data.description
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint
