from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped
from .base import BaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .student import Student
    from .teacher import Teacher
    from .academic import Department

class School(BaseModel):
    __tablename__ = "schools"
    
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255), unique=True, nullable=False)
    website = Column(String(255))
    principal_name = Column(String(255))
    join_code = Column(String(10), unique=True, nullable=False)
    logo_url = Column(String(500))
    is_boarding_school = Column(Boolean, default=False)
    school_type = Column(String(50))  # primary, secondary, mixed
    settings = Column(JSON, default={})
    is_approved = Column(Boolean, default=False)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="school")
    students: Mapped[List["Student"]] = relationship("Student", back_populates="school")
    teachers: Mapped[List["Teacher"]] = relationship("Teacher", back_populates="school")
    departments: Mapped[List["Department"]] = relationship("Department", back_populates="school")
    subscription: Mapped["SchoolSubscription"] = relationship("SchoolSubscription", back_populates="school", uselist=False)

class SchoolSubscription(BaseModel):
    __tablename__ = "school_subscriptions"
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    plan_name = Column(String(100), nullable=False)
    max_students = Column(Integer)
    max_teachers = Column(Integer)
    features = Column(JSON, default={})
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_trial = Column(Boolean, default=False)
    
    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="subscription")
