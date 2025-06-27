from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ProspectiveApplicantBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    school_id: int

class ProspectiveApplicantCreate(ProspectiveApplicantBase):
    password: str

class ProspectiveApplicantLogin(BaseModel):
    email: EmailStr
    password: str

class ProspectiveApplicantResponse(ProspectiveApplicantBase):
    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProspectiveApplicantToken(BaseModel):
    access_token: str
    token_type: str
    applicant: ProspectiveApplicantResponse
