from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# Base schema for a single field in the form structure
class FormField(BaseModel):
    field_name: str
    label: str
    type: str
    required: bool
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    min_length: Optional[int] = None

# Schema for creating a new AdmissionFormTemplate
class AdmissionFormTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    form_structure: List[FormField]
    is_default: bool = False

# Schema for updating an existing AdmissionFormTemplate
class AdmissionFormTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    form_structure: Optional[List[FormField]] = None
    is_default: Optional[bool] = None

# Schema for reading/returning an AdmissionFormTemplate
class AdmissionFormTemplate(BaseModel):
    id: int
    school_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    is_active: bool
    form_structure: List[FormField]
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ApplicationStatusEnum(str, Enum):
    SUBMITTED = "Submitted"
    REVIEWING = "Reviewing"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    WAITLISTED = "Waitlisted"

class AdmissionApplicationCreate(BaseModel):
    admission_form_template_id: int
    form_data: Dict[str, Any]
    prospective_applicant_id: int

class AdmissionApplicationUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class AdmissionApplication(BaseModel):
    id: int
    admission_form_template_id: int
    form_data: Dict[str, Any]
    prospective_applicant_id: int
    status: ApplicationStatusEnum = ApplicationStatusEnum.SUBMITTED
    submission_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationDocumentBase(BaseModel):
    document_type: str
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

class ApplicationDocumentCreate(ApplicationDocumentBase):
    application_id: int

class ApplicationDocument(ApplicationDocumentBase):
    id: int
    application_id: int
    school_id: int
    uploaded_at: Optional[datetime] = None
    is_verified: bool = False
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatusEnum

    @field_validator('status', mode='before')
    @classmethod
    def title_case_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class ApplicationApproval(BaseModel):
    create_student_record: bool = True
    student_id: Optional[str] = None
    class_id: Optional[int] = None
    admission_date: Optional[date] = None

class PublicApplicationStatus(BaseModel):
    id: int
    status: ApplicationStatusEnum

    class Config:
        from_attributes = True