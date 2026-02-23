from sqlalchemy import Column, String, Integer ,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base
from app.models.area import Area
from app.models.category import Category


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(String, nullable=False)  # user / professional / admin
    status = Column(String, default="active")
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=True)
    area = relationship("Area")

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category")
    experience = Column(Integer, nullable=True)
