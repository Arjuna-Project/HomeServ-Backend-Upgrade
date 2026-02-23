from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    role: str
    area_id: int
    category_id: Optional[int] = None
    experience: Optional[int] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    role: str
    status: Optional[str]
    category_id: Optional[int] = None
    experience: Optional[int] = None

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    phone: str 
    category_id: Optional[int] = None
    experience: Optional[int] = None
    
    class Config:
        from_attributes = True