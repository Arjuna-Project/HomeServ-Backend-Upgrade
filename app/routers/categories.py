from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.category import Category
from app.utils.dependencies import get_db, get_current_user
from app.utils.dependencies import admin_required
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()

    return [
        {
            "id": cat.id,
            "name": cat.name
        }
        for cat in categories
    ]


@router.post("", response_model=CategoryResponse)
def add_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    admin_required(current_user)

    cat = Category(name=data.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    return cat


@router.delete("/{id}")
def delete_category(id: int,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):

    admin_required(current_user)

    category = db.query(Category).filter(Category.id == id).first()
    if not category:
        raise HTTPException(404, "Category not found")

    db.delete(category)
    db.commit()

    return {"message": "Category deleted"}
