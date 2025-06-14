from __future__ import annotations
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Time
from sqlalchemy.orm import relationship, Mapped
from .base import TenantBaseModel
from typing import List, TYPE_CHECKING
from datetime import time

if TYPE_CHECKING:
    from .attendance import AttendanceRecord
    from .academic import Class, Subject, AcademicSession
    from .teacher import Teacher

class Period(TenantBaseModel):
    __tablename__ = "periods"
    
    name = Column(String(100), nullable=False)  # Period 1, Period 2, etc.
    start_time: time = Column(Time, nullable=False)
    end_time: time = Column(Time, nullable=False)
    order_number = Column(Integer, nullable=False)
    is_break = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    timetable_entries: Mapped[List["TimetableEntry"]] = relationship("TimetableEntry", back_populates="period")
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="period")

class TimetableEntry(TenantBaseModel):
    __tablename__ = "timetable_entries"
    
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 1=Monday, 7=Sunday
    room_number = Column(String(20))
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"), nullable=False)
    notes = Column(Text)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    class_assigned: Mapped["Class"] = relationship("Class", back_populates="timetable_entries")
    subject: Mapped["Subject"] = relationship("Subject")
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="timetable_entries")
    period: Mapped["Period"] = relationship("Period", back_populates="timetable_entries")
    academic_session: Mapped["AcademicSession"] = relationship("AcademicSession")
