from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# --- Enums for Student Schemas ---
class BoardingStatusEnum(str, Enum):
    DAY = "Day"
    BOARDING = "Boarding"

class StudentStatusEnum(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    GRADUATED = "Graduated"
    WITHDRAWN = "Withdrawn"

class RelationshipTypeEnum(str, Enum):
    FATHER = "Father"
    MOTHER = "Mother"
    GUARDIAN = "Guardian"
    OTHER = "Other"

class BloodGroupEnum(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"

class StudentBase(BaseModel):
    student_id: str
    admission_number: Optional[str] = None
    class_id: Optional[int] = None
    admission_date: Optional[date] = None
    boarding_status: Optional[BoardingStatusEnum] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    previous_school: Optional[str] = None
    blood_group: Optional[BloodGroupEnum] = None

    @field_validator('boarding_status', 'emergency_contact_relationship', mode='before')
    @classmethod
    def title_case_fields(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v

    @field_validator('blood_group', mode='before')
    @classmethod
    def upper_case_blood_group(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v
    allergies: Optional[str] = None
    medications: Optional[str] = None
    special_needs: Optional[str] = None

class StudentCreate(StudentBase):
    user_id: int

class StudentUpdate(BaseModel):
    admission_number: Optional[str] = None
    class_id: Optional[int] = None
    boarding_status: Optional[BoardingStatusEnum] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    previous_school: Optional[str] = None
    blood_group: Optional[BloodGroupEnum] = None

    @field_validator('boarding_status', 'emergency_contact_relationship', mode='before')
    @classmethod
    def title_case_fields(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v

    @field_validator('blood_group', mode='before')
    @classmethod
    def upper_case_blood_group(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v
    allergies: Optional[str] = None
    medications: Optional[str] = None
    special_needs: Optional[str] = None
    medical_info: Optional[Dict[str, Any]] = None

class Student(StudentBase):
    id: int
    user_id: int
    school_id: int
    status: StudentStatusEnum = StudentStatusEnum.ACTIVE

    @field_validator('status', mode='before')
    @classmethod
    def title_case_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
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
    relationship_type: RelationshipTypeEnum

    @field_validator('relationship_type', mode='before')
    @classmethod
    def title_case_relationship(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
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
    status: StudentStatusEnum

    @field_validator('status', mode='before')
    @classmethod
    def title_case_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
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
