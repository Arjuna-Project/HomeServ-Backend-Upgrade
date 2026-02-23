from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.routers.admin import admin_required
from app.utils.dependencies import get_current_user, get_db
from app.schemas.service import ServiceCreate, ServiceResponse
from app.models.service import Service
from app.models.user import User

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("", response_model=ServiceResponse)
def create_service(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    service = Service(
        name=data.name,
        description=data.description,
        price=data.price,
        category_id=data.category_id
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@router.get("")
def get_services(db: Session = Depends(get_db)):

    services = db.query(Service).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "price": s.price,
            "category_id": s.category_id,
            "category_name": s.category.name if s.category else None
        }
        for s in services
    ]

@router.get("/{id}")
def get_service(id: int, db: Session = Depends(get_db)):

    service = db.query(Service).filter(Service.id == id).first()
    if not service:
        raise HTTPException(404, "Service not found")

    return {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "price": service.price,
        "category_name": service.category.name if service.category else None
    }


@router.delete("/{id}")
def delete_service(id: int,
                   db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):

    admin_required(current_user)

    service = db.query(Service).filter(Service.id == id).first()
    if not service:
        raise HTTPException(404, "Service not found")

    db.delete(service)
    db.commit()

    return {"message": "Service deleted"}
