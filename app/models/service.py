from sqlalchemy import Column, String, Text, Float, ForeignKey, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)

    description = Column(Text, nullable=False)

    price = Column(Float, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # Relationship
    category = relationship("Category", backref="services")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
