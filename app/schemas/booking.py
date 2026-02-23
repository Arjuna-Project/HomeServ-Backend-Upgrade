from pydantic import BaseModel
from datetime import datetime


class BookingBase(BaseModel):
    service_id: int
    booking_type: str
    date: str
    time: str


class BookingCreate(BookingBase):
    pass


class BookingOut(BookingBase):
    id: int
    user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
