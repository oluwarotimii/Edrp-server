from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SchoolType(str, Enum):
    DAY = "Day"
    BOARDING = "Boarding"
    NURSERY = "Nursery"
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    TERTIARY = "Tertiary"
    DAY_AND_BOARDING = "Day & Boarding"

class SchoolBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: EmailStr
    website: Optional[str] = None
    principal_name: Optional[str] = None
    school_type: SchoolType = SchoolType.DAY

    @field_validator('school_type', mode='before')
    @classmethod
    def title_case_school_type(cls, v: str) -> str:
        """Ensure school_type is always in title case to match the Enum."""
        if isinstance(v, str):
            return v.title()
        return v

class SchoolCreate(SchoolBase):
    admin_first_name: str = Field(..., min_length=2)
    admin_last_name: str = Field(..., min_length=2)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    principal_name: Optional[str] = None
    school_type: Optional[SchoolType] = None
    settings: Optional[Dict[str, Any]] = None

class School(SchoolBase):
    id: int
    join_code: str
    logo_url: Optional[str] = None
    settings: Dict[str, Any] = {}
    is_approved: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SchoolResponse(School):
    pass

class JoinSchoolRequest(BaseModel):
    join_code: str
    role: str = "student"

class SchoolSubscriptionBase(BaseModel):
    plan_name: str
    max_students: Optional[int] = None
    max_teachers: Optional[int] = None
    features: Dict[str, Any] = {}
    is_trial: bool = False

class SchoolSubscription(SchoolSubscriptionBase):
    id: int
    school_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True
