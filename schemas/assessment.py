from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class AssessmentSchemeBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False

class AssessmentSchemeCreate(AssessmentSchemeBase):
    pass

class AssessmentSchemeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None

class AssessmentScheme(AssessmentSchemeBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class AssessmentComponentBase(BaseModel):
    name: str
    weight_percentage: float
    max_score: float = 100.0

class AssessmentComponentCreate(AssessmentComponentBase):
    scheme_id: int

class AssessmentComponentUpdate(BaseModel):
    name: Optional[str] = None
    weight_percentage: Optional[float] = None
    max_score: Optional[float] = None

class AssessmentComponent(AssessmentComponentBase):
    id: int
    scheme_id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class GradingScaleBase(BaseModel):
    grade: str
    min_score: float
    max_score: float
    description: Optional[str] = None
    gpa_value: Optional[float] = None

    @field_validator('grade', mode='before')
    @classmethod
    def uppercase_grade(cls, v: str) -> str:
        """Ensure grade is always in uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v

class GradingScaleCreate(GradingScaleBase):
    pass

class GradingScaleUpdate(BaseModel):
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    description: Optional[str] = None
    gpa_value: Optional[float] = None

class GradingScale(GradingScaleBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class AssessmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    subject_id: int
    class_id: int
    term_id: int
    component_id: int
    max_score: float
    date_conducted: Optional[date] = None
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = None

class AssessmentCreate(AssessmentBase):
    pass

class AssessmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_score: Optional[float] = None
    date_conducted: Optional[date] = None
    instructions: Optional[str] = None
    duration_minutes: Optional[int] = None

class Assessment(AssessmentBase):
    id: int
    school_id: int
    is_published: bool = False
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ScoreBase(BaseModel):
    assessment_id: int
    student_id: int
    score: float
    remarks: Optional[str] = None

class ScoreCreate(ScoreBase):
    pass

class ScoreUpdate(BaseModel):
    score: Optional[float] = None
    remarks: Optional[str] = None

class Score(ScoreBase):
    id: int
    school_id: int
    recorded_by: Optional[int] = None
    recorded_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class BatchScoreCreate(BaseModel):
    assessment_id: int
    scores: List[Dict[str, Any]]  # [{"student_id": 1, "score": 85, "remarks": "Good"}]

class SchemeAssignment(BaseModel):
    scheme_id: int

class StudentResults(BaseModel):
    student_id: int
    student_name: str
    assessments: List[Dict[str, Any]]
    total_score: float
    average_score: float
    grade: str

    @field_validator('grade', mode='before')
    @classmethod
    def uppercase_grade(cls, v: str) -> str:
        """Ensure grade is always in uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v
