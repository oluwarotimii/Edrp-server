from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class StudentBase(BaseModel):
    student_id: str
    admission_number: Optional[str] = None
    class_id: Optional[int] = None
    admission_date: Optional[date] = None
    boarding_status: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    previous_school: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    special_needs: Optional[str] = None

class StudentCreate(StudentBase):
    user_id: int

class StudentUpdate(BaseModel):
    admission_number: Optional[str] = None
    class_id: Optional[int] = None
    boarding_status: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    previous_school: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    special_needs: Optional[str] = None
    medical_info: Optional[Dict[str, Any]] = None

class Student(StudentBase):
    id: int
    user_id: int
    school_id: int
    status: str = "active"
    medical_info: Dict[str, Any] = {}
    graduation_date: Optional[date] = None
    withdrawal_date: Optional[date] = None
    withdrawal_reason: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class StudentParentBase(BaseModel):
    parent_user_id: int
    relationship_type: str
    is_primary_contact: bool = False
    can_pick_up: bool = True

class StudentParentCreate(StudentParentBase):
    student_id: int

class StudentParent(StudentParentBase):
    id: int
    student_id: int
    school_id: int

    class Config:
        from_attributes = True

class StudentCustomFieldBase(BaseModel):
    field_name: str
    field_value: Optional[str] = None
    field_type: str = "text"

class StudentCustomFieldCreate(StudentCustomFieldBase):
    student_id: int

class StudentCustomField(StudentCustomFieldBase):
    id: int
    student_id: int
    school_id: int

    class Config:
        from_attributes = True

class StudentSubjectEnrollmentBase(BaseModel):
    subject_id: int
    academic_session_id: int
    enrollment_date: Optional[date] = None
    is_core_subject: bool = False

class StudentSubjectEnrollmentCreate(StudentSubjectEnrollmentBase):
    student_id: int

class StudentSubjectEnrollment(StudentSubjectEnrollmentBase):
    id: int
    student_id: int
    school_id: int

    class Config:
        from_attributes = True

class StudentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    effective_date: Optional[date] = None

class StudentGraduation(BaseModel):
    graduation_date: date
    ceremony_id: Optional[int] = None
    notes: Optional[str] = None

class StudentWithdrawal(BaseModel):
    withdrawal_date: date
    reason: str
    transfer_school: Optional[str] = None
