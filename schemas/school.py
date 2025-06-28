from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List
from schemas.result_settings import ResultSettings
from datetime import datetime
from enum import Enum
import re


class SchoolType(str, Enum):
    DAY = "Day"
    BOARDING = "Boarding"
    NURSERY = "Nursery"
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    TERTIARY = "Tertiary"
    DAY_AND_BOARDING = "Day & Boarding"

class SubdomainBase(BaseModel):
    """Base model for subdomain validation"""
    
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        if not v:
            raise ValueError("Subdomain cannot be empty")
            
        v = v.lower().strip()
        
        # Length validation
        if len(v) < 3:
            raise ValueError("Subdomain must be at least 3 characters long")
        if len(v) > 63:
            raise ValueError("Subdomain cannot exceed 63 characters")
            
        # Format validation
        if not re.match(r'^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$', v):
            raise ValueError(
                "Subdomain can only contain lowercase letters, numbers, and hyphens. "
                "It must start and end with a letter or number."
            )
            
        # Reserved names
        reserved = [
            'www', 'api', 'admin', 'app', 'mail', 'smtp', 'pop', 'imap', 'webmail',
            'dev', 'staging', 'test', 'prod', 'production', 'staging', 'beta'
        ]
        if v in reserved:
            raise ValueError(f"'{v}' is a reserved subdomain")
            
        return v

class SchoolBase(SubdomainBase):
    name: str = Field(..., min_length=2, max_length=255)
    subdomain: Optional[str] = Field(
        None,
        min_length=3,
        max_length=63,
        pattern=r'^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$',
        description="URL-friendly subdomain (lowercase letters, numbers, and hyphens only)"
    )
    address: Optional[str] = None
    phone: Optional[str] = None
    email: EmailStr
    website: Optional[str] = None
    principal_name: Optional[str] = None
    school_type: SchoolType = SchoolType.DAY
    
    @model_validator(mode='after')
    def generate_subdomain_if_needed(self) -> 'SchoolBase':
        # Local import to avoid circular dependency
        from models.school import School as SchoolModel
        if not self.subdomain and hasattr(self, 'name'):
            self.subdomain = SchoolModel.generate_subdomain(self.name)
        return self
    
    @field_validator('subdomain', mode='before')
    @classmethod
    def clean_subdomain(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        return super().validate_subdomain(v.lower().strip())

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
    grading_profile_id: Optional[int] = None
    
    @model_validator(mode='after')
    def validate_subdomain_availability(self, db) -> 'SchoolCreate':
        # Local import to avoid circular dependency
        from models.school import School as SchoolModel
        from sqlalchemy import exists
        from sqlalchemy.orm import Session
        
        if self.subdomain and db is not None:
            exists = db.query(
                exists().where(SchoolModel.subdomain == self.subdomain)
            ).scalar()
            if exists:
                raise ValueError(f"Subdomain '{self.subdomain}' is already taken")
        return self

class SchoolUpdate(SubdomainBase):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    subdomain: Optional[str] = Field(
        None,
        min_length=3,
        max_length=63,
        pattern=r'^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$',
        description="URL-friendly subdomain (lowercase letters, numbers, and hyphens only)"
    )
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    principal_name: Optional[str] = None
    school_type: Optional[SchoolType] = None
    settings: Optional[ResultSettings] = None
    grading_profile_id: Optional[int] = None
    
    @field_validator('subdomain', mode='before')
    @classmethod
    def clean_subdomain(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        return super().validate_subdomain(v.lower().strip())

class School(SchoolBase):
    id: int
    subdomain: str = Field(..., min_length=3, max_length=63)
    join_code: str
    logo_url: Optional[str] = None
    settings: ResultSettings = Field(default_factory=ResultSettings) # Use default_factory for mutable defaults
    is_approved: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    @property
    def base_url(self) -> str:
        """Get the full base URL for this school"""
        from core.config import settings
        if settings.ENVIRONMENT == 'production':
            return f"https://{self.subdomain}.{settings.ROOT_DOMAIN}"
        return f"http://{self.subdomain}.{settings.ROOT_DOMAIN}:{settings.PORT}"

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


class ReportTemplateBase(BaseModel):
    name: str
    template_type: str
    html_content: str
    is_active: bool = True
    description: Optional[str] = None

class ReportTemplateCreate(ReportTemplateBase):
    pass

class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_type: Optional[str] = None
    html_content: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class ReportTemplate(ReportTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True