from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship, Mapped
from .base import BaseModel
from typing import List, TYPE_CHECKING
from datetime import datetime # Added import
from sqlalchemy import Enum
from schemas.subscription import SubscriptionStatusEnum

if TYPE_CHECKING:
    from .user import User
    from .student import Student
    from .teacher import Teacher
    from .academic import Department

class School(BaseModel):
    __tablename__ = "schools"
    
    name = Column(String(255), nullable=False)
    subdomain = Column(String(63), unique=True, nullable=False, index=True)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255), unique=True, nullable=False)
    website = Column(String(255))
    principal_name = Column(String(255))
    join_code = Column(String(10), unique=True, nullable=False)
    logo_url = Column(String(500))
    school_type = Column(String(50), nullable=False, default='Day')  # e.g., 'Day' or 'Boarding'
    settings = Column(JSON, default={})
    is_approved = Column(Boolean, default=False)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="school")
    students: Mapped[List["Student"]] = relationship("Student", back_populates="school")
    teachers: Mapped[List["Teacher"]] = relationship("Teacher", back_populates="school")
    departments: Mapped[List["Department"]] = relationship("Department", back_populates="school")
    subscription: Mapped["SchoolSubscription"] = relationship("SchoolSubscription", back_populates="school", uselist=False)
    
    @staticmethod
    def is_valid_subdomain(subdomain: str) -> bool:
        """Check if a subdomain is valid"""
        import re
        if not subdomain or len(subdomain) > 63 or len(subdomain) < 3:
            return False
        # Must start and end with alphanumeric, can contain hyphens in between
        pattern = r'^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?'

        return bool(re.match(pattern, subdomain))
    
    @classmethod
    def generate_subdomain(cls, name: str) -> str:
        """Generate a URL-friendly subdomain from school name"""
        import re
        import unicodedata
        
        # Convert to ASCII and lowercase
        subdomain = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower()
        
        # Replace spaces and special characters with hyphens
        subdomain = re.sub(r'[^a-z0-9-]', '-', subdomain)
        
        # Remove consecutive hyphens
        subdomain = re.sub(r'-+', '-', subdomain)
        
        # Remove leading/trailing hyphens
        subdomain = subdomain.strip('-')
        
        # Ensure it's not empty
        if not subdomain:
            subdomain = 'school'
            
        # Ensure it's not too long
        if len(subdomain) > 63:
            subdomain = subdomain[:63].rstrip('-')
            
        return subdomain

class SchoolSubscription(BaseModel):
    __tablename__ = "school_subscriptions"
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    
    # Subscription details
    status = Column(Enum(SubscriptionStatusEnum), default=SubscriptionStatusEnum.ACTIVE)  # Use Enum
    is_trial = Column(Boolean, default=False)
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    
    # Payment details
    paystack_subscription_code = Column(String(100), nullable=True)
    paystack_customer_code = Column(String(100), nullable=True)
    payment_method = Column(String(50), nullable=True)
    
    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="school_subscriptions")
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        now = datetime.utcnow()
        return self.status == SubscriptionStatusEnum.ACTIVE and (self.end_date is None or self.end_date >= now)

