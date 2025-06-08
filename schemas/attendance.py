from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time

class AuthenticLocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    radius_meters: int = 100
    is_default: bool = False

class AuthenticLocationCreate(AuthenticLocationBase):
    pass

class AuthenticLocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = None
    is_default: Optional[bool] = None

class AuthenticLocation(AuthenticLocationBase):
    id: int
    school_id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class LocationVerificationRequest(BaseModel):
    latitude: float
    longitude: float
    location_id: Optional[int] = None

class AttendanceRecordBase(BaseModel):
    student_id: int
    date: date
    session_name: Optional[str] = None
    status: str
    period_id: Optional[int] = None
    subject_id: Optional[int] = None
    notes: Optional[str] = None

class AttendanceRecordCreate(AttendanceRecordBase):
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class AttendanceRecordUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class AttendanceRecord(AttendanceRecordBase):
    id: int
    school_id: int
    marked_by: Optional[int] = None
    marked_at: Optional[datetime] = None
    location_verified: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class BulkAttendanceCreate(BaseModel):
    date: date
    session_name: Optional[str] = None
    period_id: Optional[int] = None
    subject_id: Optional[int] = None
    attendance_records: List[dict]  # {student_id, status, notes}
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TeacherAttendanceBase(BaseModel):
    teacher_id: int
    date: date
    status: str
    notes: Optional[str] = None

class TeacherAttendanceCreate(TeacherAttendanceBase):
    clock_in_latitude: Optional[float] = None
    clock_in_longitude: Optional[float] = None

class TeacherAttendanceUpdate(BaseModel):
    clock_out_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    clock_out_latitude: Optional[float] = None
    clock_out_longitude: Optional[float] = None

class TeacherAttendance(TeacherAttendanceBase):
    id: int
    school_id: int
    clock_in_time: Optional[datetime] = None
    clock_out_time: Optional[datetime] = None
    total_hours: Optional[float] = None
    location_verified: bool = False
    clock_in_latitude: Optional[float] = None
    clock_in_longitude: Optional[float] = None
    clock_out_latitude: Optional[float] = None
    clock_out_longitude: Optional[float] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class AttendanceStatistics(BaseModel):
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    excused_days: int
    attendance_percentage: float
    period: str  # daily, weekly, monthly, termly
