from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from schemas.assessment import AssessmentScheme, GradingScale

class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    head_teacher_id: Optional[int] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    head_teacher_id: Optional[int] = None

class Department(DepartmentBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ClassBase(BaseModel):
    name: str
    description: Optional[str] = None
    class_teacher_id: Optional[int] = None
    capacity: Optional[int] = None
    room_number: Optional[str] = None
    grade_level: Optional[int] = None

class ClassCreate(ClassBase):
    pass

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    class_teacher_id: Optional[int] = None
    capacity: Optional[int] = None
    room_number: Optional[str] = None
    grade_level: Optional[int] = None

class Class(ClassBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class SubjectBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[int] = None
    is_core: bool = False
    credit_units: int = 1

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[int] = None
    is_core: Optional[bool] = None
    credit_units: Optional[int] = None

class Subject(SubjectBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class AcademicSessionBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_current: bool = False
    is_locked: bool = False

class AcademicSessionCreate(AcademicSessionBase):
    pass

class AcademicSessionUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    is_locked: Optional[bool] = None

class AcademicSession(AcademicSessionBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime
    locked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TermBase(BaseModel):
    name: str
    academic_session_id: int
    start_date: date
    end_date: date
    is_current: bool = False
    is_locked: bool = False

class TermCreate(TermBase):
    pass

class TermUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    is_locked: Optional[bool] = None

class Term(TermBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime
    locked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubjectResultBase(BaseModel):
    student_id: int
    subject_id: int
    term_id: int
    total_score: float
    grade: str
    gpa: Optional[float] = None
    rank: Optional[int] = None
    remarks: Optional[str] = None

class SubjectResultCreate(SubjectResultBase):
    pass

class SubjectResultUpdate(BaseModel):
    total_score: Optional[float] = None
    grade: Optional[str] = None
    gpa: Optional[float] = None
    rank: Optional[int] = None
    remarks: Optional[str] = None

class SubjectResult(SubjectResultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TermResultBase(BaseModel):
    student_id: int
    term_id: int
    total_gpa: Optional[float] = None
    total_score: Optional[float] = None
    overall_grade: Optional[str] = None
    position_in_class: Optional[int] = None
    remarks: Optional[str] = None

class TermResultCreate(TermResultBase):
    pass

class TermResultUpdate(BaseModel):
    total_gpa: Optional[float] = None
    total_score: Optional[float] = None
    overall_grade: Optional[str] = None
    position_in_class: Optional[int] = None
    remarks: Optional[str] = None

class TermResult(TermResultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentCumulativeResultBase(BaseModel):
    student_id: int
    academic_session_id: int
    cumulative_gpa: Optional[float] = None
    cumulative_score: Optional[float] = None
    overall_cumulative_grade: Optional[str] = None
    overall_cumulative_position: Optional[int] = None

class StudentCumulativeResultCreate(StudentCumulativeResultBase):
    pass

class StudentCumulativeResultUpdate(BaseModel):
    cumulative_gpa: Optional[float] = None
    cumulative_score: Optional[float] = None
    overall_cumulative_grade: Optional[str] = None
    overall_cumulative_position: Optional[int] = None

class StudentCumulativeResult(StudentCumulativeResultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GradingProfileBase(BaseModel):
    name: str
    description: Optional[str] = None
    uses_gpa: bool = False
    gpa_scale: Optional[float] = 4.0
    allows_astar_grade: bool = False
    remarks_are_mandatory: bool = False

class GradingProfileCreate(GradingProfileBase):
    pass

class GradingProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    uses_gpa: Optional[bool] = None
    gpa_scale: Optional[float] = None
    allows_astar_grade: Optional[bool] = None
    remarks_are_mandatory: Optional[bool] = None

class GradingProfile(GradingProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
