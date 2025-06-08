from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, date

class TeacherBase(BaseModel):
    employee_id: str
    department_id: Optional[int] = None
    hire_date: Optional[date] = None
    teaching_qualification: Optional[str] = None
    specialization: Optional[str] = None
    years_experience: Optional[int] = None
    salary_grade: Optional[str] = None
    contract_type: Optional[str] = "permanent"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class TeacherCreate(TeacherBase):
    user_id: int

class TeacherUpdate(BaseModel):
    department_id: Optional[int] = None
    teaching_qualification: Optional[str] = None
    specialization: Optional[str] = None
    years_experience: Optional[int] = None
    salary_grade: Optional[str] = None
    contract_type: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    bank_details: Optional[Dict[str, Any]] = None
    certifications: Optional[Dict[str, Any]] = None

class Teacher(TeacherBase):
    id: int
    user_id: int
    school_id: int
    status: str = "active"
    bank_details: Dict[str, Any] = {}
    certifications: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class TeacherAssignmentBase(BaseModel):
    subject_id: int
    class_id: int
    academic_session_id: int
    is_class_teacher: bool = False
    assignment_date: Optional[date] = None

class TeacherAssignmentCreate(TeacherAssignmentBase):
    teacher_id: int

class TeacherAssignment(TeacherAssignmentBase):
    id: int
    teacher_id: int
    school_id: int

    class Config:
        from_attributes = True

class TeacherStatusUpdate(BaseModel):
    status: str
    effective_date: Optional[date] = None
    notes: Optional[str] = None
