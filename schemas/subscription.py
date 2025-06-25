from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime

class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    price_monthly: float = Field(..., gt=0)
    price_yearly: Optional[float] = Field(None, gt=0)
    
    # Feature limits
    max_students: int = Field(..., gt=0)
    max_teachers: int = Field(..., gt=0)
    max_storage_mb: int = Field(1024, gt=0)  # Default 1GB
    
    # Features
    features: Dict[str, Any] = {}
    is_active: bool = True
    is_default: bool = False
    
    class Config:
        from_attributes = True

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price_monthly: Optional[float] = Field(None, gt=0)
    price_yearly: Optional[float] = Field(None, gt=0)
    max_students: Optional[int] = Field(None, gt=0)
    max_teachers: Optional[int] = Field(None, gt=0)
    max_storage_mb: Optional[int] = Field(None, gt=0)
    features: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SchoolSubscriptionBase(BaseModel):
    plan_id: int
    is_trial: bool = False
    auto_renew: bool = True

class SchoolSubscriptionCreate(SchoolSubscriptionBase):
    payment_method: str  # e.g., 'card', 'bank_transfer'
    paystack_authorization_code: Optional[str] = None  # For card payments

class SchoolSubscriptionResponse(SchoolSubscriptionBase):
    id: int
    school_id: int
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SubscriptionStatusResponse(BaseModel):
    is_active: bool
    status: str
    plan_name: str
    start_date: datetime
    end_date: Optional[datetime]
    days_remaining: Optional[int]
    max_students: int
    max_teachers: int
    max_storage_mb: int
    current_usage: Dict[str, int]  # Current usage stats
    
    class Config:
        from_attributes = True
