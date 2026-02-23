from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.dependencies import get_current_user, get_db
from app.schemas.booking import BookingCreate, BookingOut
from app.models.booking import Booking
from app.models.user import User
from app.models.service import Service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingOut)
def create_booking(
    data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    booking = Booking(
    user_id=current_user.id,
    service_id=data.service_id,
    area_id=current_user.area_id,  # 🔥 take from user
    date=data.date,
    time=data.time,
    booking_type=data.booking_type
    )


    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking


@router.get("/my")
def my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure ID is correct type
    user_id = int(current_user.id)

    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == user_id)
        .all()
    )

    if not bookings:
        return []

    result = []

    for booking in bookings:
        service = db.query(Service).filter(
            Service.id == booking.service_id
        ).first()

        result.append({
            "id": booking.id,
            "service_name": service.name if service else "Unknown",
            "date": booking.date,
            "time": booking.time,
            "status": booking.status
        })

    return result


@router.get("/professional")
def professional_all_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "professional":
        raise HTTPException(status_code=403, detail="Professional only")

    bookings = db.query(Booking)\
        .join(Service, Booking.service_id == Service.id)\
        .join(User, Booking.user_id == User.id)\
        .filter(
            (
                (Booking.status == "pending") &
                (Booking.area_id == current_user.area_id) &
                (Service.category_id == current_user.category_id)
            )
            |
            (
                Booking.professional_id == current_user.id
            )
        ).all()

    result = []

    for booking in bookings:
        service = db.query(Service).filter(Service.id == booking.service_id).first()
        user = db.query(User).filter(User.id == booking.user_id).first()

        result.append({
            "id": booking.id,
            "service_name": service.name if service else None,
            "user_name": user.name if user else None,
            "date": booking.date,
            "time": booking.time,
            "status": booking.status
        })

    return result


@router.put("/{booking_id}/accept")
def accept_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = "accepted"
    booking.professional_id = current_user.id

    db.commit()

    return {"message": "Booking accepted"}

@router.put("/{booking_id}/complete")
def complete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.professional_id == current_user.id
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = "completed"
    db.commit()

    return {"message": "Booking completed"}


