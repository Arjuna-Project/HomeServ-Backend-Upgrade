from pydantic import BaseModel
from uuid import UUID


class ServiceCreate(BaseModel):
    name: str
    description: str
    price: int
    category_id: int


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int
    category_id: int

    class Config:
        from_attributes = True
