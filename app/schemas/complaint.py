from pydantic import BaseModel
from uuid import UUID


class ComplaintCreate(BaseModel):
    booking_id: int
    description: str


class ComplaintResponse(BaseModel):
    id: int
    booking_id: int
    description: str
    status: str

    class Config:
        from_attributes = True
