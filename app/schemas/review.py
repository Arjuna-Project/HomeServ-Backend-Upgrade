from pydantic import BaseModel
from uuid import UUID


class ReviewCreate(BaseModel):
    booking_id: int
    rating: int
    comment: str


class ReviewResponse(BaseModel):
    id: int
    booking_id: int
    rating: int
    comment: str

    class Config:
        from_attributes = True
