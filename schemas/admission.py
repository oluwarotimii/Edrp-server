from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class AdmissionApplicationBase(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: date
    gender: str
    address: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    
    # Parent/Guardian Information
    parent_first_name: str
    parent_last_name: str
    parent_phone: str
    parent_email: EmailStr
    parent_occupation: Optional[str] = None
    parent_address: Optional[str] = None
    relationship_to_student: str
    
    # Academic Information
    previous_school: Optional[str] = None
    class_applying_for: Optional[int] = None
    academic_session_id: Optional[int] = None
    
    # Additional Information
    medical_conditions: Optional[str] = None
    special_needs: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = {}

class AdmissionApplicationCreate(AdmissionApplicationBase):
    pass

class AdmissionApplicationUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class AdmissionApplication(AdmissionApplicationBase):
    id: int
    application_number: str
    school_id: int
    status: str = "submitted"
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
    status: str
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class ApplicationApproval(BaseModel):
    create_student_record: bool = True
    student_id: Optional[str] = None
    class_id: Optional[int] = None
    admission_date: Optional[date] = None
