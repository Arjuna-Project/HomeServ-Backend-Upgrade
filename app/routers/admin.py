from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.utils.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.booking import Booking
from app.models.category import Category
from app.models.service import Service
from app.schemas.category import CategoryCreate
from app.schemas.service import ServiceCreate

router = APIRouter(prefix="/admin", tags=["Admin"])


def admin_required(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("/stats")
def stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    admin_required(current_user)

    return {
        "total_users": db.query(User).filter(User.role == "user").count(),
        "total_professionals": db.query(User)
        .filter(User.role == "professional")
        .count(),
        "total_bookings": db.query(Booking).count(),
    }


@router.get("/users")
def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_required(current_user)

    offset = (page - 1) * limit

    total = db.query(User).filter(User.role == "user").count()

    users = db.query(User).filter(User.role == "user").offset(offset).limit(limit).all()

    return {"total": total, "page": page, "limit": limit, "data": users}

@router.get("/professionals")
def get_professionals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_required(current_user)

    professionals = db.query(User).filter(
        User.role == "professional"
    ).all()

    result = []

    for pro in professionals:
        result.append({
            "id": pro.id,
            "name": pro.name,
            "email": pro.email,
            "category": pro.category.name if pro.category else "Not Assigned",
            "experience": pro.experience or 0,
            "status": pro.status
        })

    return {"data": result}


@router.get("/bookings")
def all_bookings(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    admin_required(current_user)

    bookings = db.query(Booking).all()

    result = []

    for b in bookings:
        user = db.query(User).filter(User.id == b.user_id).first()
        professional = db.query(User).filter(User.id == b.professional_id).first()
        service = db.query(Service).filter(Service.id == b.service_id).first()

        result.append(
            {
                "id": b.id,
                "user_name": user.name if user else None,
                "professional_name": professional.name if professional else None,
                "service_name": service.name if service else None,
                "date": b.date,
                "time": b.time,
                "status": b.status,
            }
        )

    return {"total": len(result), "data": result}


@router.post("/categories")
def add_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_required(current_user)

    cat = Category(name=data["name"])
    db.add(cat)
    db.commit()
    db.refresh(cat)

    return cat


@router.get("/categories")
def get_categories(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    admin_required(current_user)

    return db.query(Category).all()


@router.post("/services")
def add_service(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_required(current_user)

    service = Service(**data)
    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@router.get("/services")
def get_services(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    admin_required(current_user)

    return db.query(Service).all()

@router.delete("/professionals/{user_id}")
def delete_professional(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_required(current_user)

    user = db.query(User).filter(
        User.id == user_id,
        User.role == "professional"
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Professional not found")

    db.delete(user)
    db.commit()

    return {"message": "Professional deleted successfully"}

