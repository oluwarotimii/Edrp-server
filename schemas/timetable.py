from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time

class PeriodBase(BaseModel):
    name: str
    start_time: time
    end_time: time
    order_number: int
    is_break: bool = False

class PeriodCreate(PeriodBase):
    pass

class PeriodUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    order_number: Optional[int] = None
    is_break: Optional[bool] = None

class Period(PeriodBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class TimetableEntryBase(BaseModel):
    class_id: int
    subject_id: int
    teacher_id: int
    period_id: int
    day_of_week: int
    room_number: Optional[str] = None
    academic_session_id: int
    notes: Optional[str] = None

class TimetableEntryCreate(TimetableEntryBase):
    pass

class TimetableEntryUpdate(BaseModel):
    subject_id: Optional[int] = None
    teacher_id: Optional[int] = None
    period_id: Optional[int] = None
    day_of_week: Optional[int] = None
    room_number: Optional[str] = None
    notes: Optional[str] = None

class TimetableEntry(TimetableEntryBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ClassTimetable(BaseModel):
    class_id: int
    class_name: str
    academic_session_id: int
    timetable: List[List[Optional[dict]]]  # 7 days x periods matrix

class TeacherTimetable(BaseModel):
    teacher_id: int
    teacher_name: str
    academic_session_id: int
    timetable: List[List[Optional[dict]]]  # 7 days x periods matrix
