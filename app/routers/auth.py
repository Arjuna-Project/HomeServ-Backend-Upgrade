from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin
from app.schemas.token import TokenResponse
from app.utils.hash import hash_password, verify_password
from app.utils.jwt import create_token
from app.utils.dependencies import get_db
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(data: UserRegister, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    status = "pending" if data.role == "professional" else "active"

    user = User(
    name=data.name,
    email=data.email,
    phone=data.phone,
    password=hash_password(data.password),
    role=data.role,
    status="pending" if data.role == "professional" else "active",
    area_id=data.area_id,
    category_id=data.category_id if data.role == "professional" else None,
    experience=data.experience if data.role == "professional" else None
)



    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Registered successfully"}

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "id": str(user.id),
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/login-json", response_model=TokenResponse)
def login_json(
    data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "id": str(user.id),
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

