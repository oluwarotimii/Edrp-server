from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Time
from sqlalchemy.orm import relationship
from .base import TenantBaseModel
from .attendance import AttendanceRecord

class Period(TenantBaseModel):
    __tablename__ = "periods"
    
    name = Column(String(100), nullable=False)  # Period 1, Period 2, etc.
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    order_number = Column(Integer, nullable=False)
    is_break = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    timetable_entries = relationship("TimetableEntry", back_populates="period")
    attendance_records = relationship("AttendanceRecord", back_populates="period")

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
    class_assigned = relationship("Class", back_populates="timetable_entries")
    subject = relationship("Subject")
    teacher = relationship("Teacher", back_populates="timetable_entries")
    period = relationship("Period", back_populates="timetable_entries")
    academic_session = relationship("AcademicSession")
