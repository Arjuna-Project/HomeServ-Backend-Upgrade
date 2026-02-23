from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)

    description = Column(Text, nullable=False)

    status = Column(String, default="open")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

