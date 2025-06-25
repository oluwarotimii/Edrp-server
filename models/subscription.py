from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, func
from sqlalchemy.orm import relationship
from .base import BaseModel
from typing import Dict, Any, List, Optional

class SubscriptionPlan(BaseModel):
    __tablename__ = "subscription_plans"
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    price_monthly = Column(Float, nullable=False)  # in NGN
    price_yearly = Column(Float, nullable=True)     # Optional yearly price
    
    # Feature limits
    max_students = Column(Integer, nullable=False)
    max_teachers = Column(Integer, nullable=False)
    max_storage_mb = Column(Integer, nullable=False, default=1024)  # 1GB default
    
    # Features
    features = Column(JSON, default=dict)  # Additional features as key-value pairs
    
    # Paystack integration
    paystack_plan_code = Column(String(100), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Relationships
    school_subscriptions = relationship("SchoolSubscription", back_populates="plan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price_monthly": self.price_monthly,
            "price_yearly": self.price_yearly,
            "max_students": self.max_students,
            "max_teachers": self.max_teachers,
            "max_storage_mb": self.max_storage_mb,
            "features": self.features or {},
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
