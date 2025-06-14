from __future__ import annotations
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Time, Float
from sqlalchemy.orm import relationship, Mapped
from .base import TenantBaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .student import Student
    from .user import User
    from .timetable import Period
    from .academic import Subject
    from .teacher import Teacher

class AuthenticLocation(TenantBaseModel):
    __tablename__ = "authentic_locations"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Integer, default=100)
    is_default = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

class AttendanceRecord(TenantBaseModel):
    __tablename__ = "attendance_records"
    
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False)
    session_name = Column(String(50))  # morning, afternoon, evening
    status = Column(String(20), nullable=False)  # present, absent, late, excused
    marked_by = Column(Integer, ForeignKey("users.id"))
    marked_at = Column(DateTime)
    period_id = Column(Integer, ForeignKey("periods.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    notes = Column(Text)
    location_verified = Column(Boolean, default=False)
    latitude = Column(Float)
    longitude = Column(Float)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="attendance_records")
    marker: Mapped["User"] = relationship("User")
    period: Mapped["Period"] = relationship("Period", back_populates="attendance_records")
    subject: Mapped["Subject"] = relationship("Subject")

class TeacherAttendance(TenantBaseModel):
    __tablename__ = "teacher_attendance"
    
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    date = Column(Date, nullable=False)
    clock_in_time = Column(DateTime)
    clock_out_time = Column(DateTime)
    status = Column(String(20), nullable=False)  # present, absent, late, half_day
    total_hours = Column(Float)
    notes = Column(Text)
    location_verified = Column(Boolean, default=False)
    clock_in_latitude = Column(Float)
    clock_in_longitude = Column(Float)
    clock_out_latitude = Column(Float)
    clock_out_longitude = Column(Float)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="attendance_records")
