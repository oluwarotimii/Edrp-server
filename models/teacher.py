from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, JSON
from sqlalchemy.orm import relationship
from .base import TenantBaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .school import School, Department
    from .attendance import TeacherAttendance
    from .timetable import TimetableEntry
    from .academic import Subject, Class, AcademicSession

class Teacher(TenantBaseModel):
    __tablename__ = "teachers"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    hire_date = Column(Date)
    status = Column(String(20), default="active")  # active, on_leave, resigned, terminated
    teaching_qualification = Column(String(255))
    specialization = Column(String(255))
    years_experience = Column(Integer)
    salary_grade = Column(String(20))
    contract_type = Column(String(20))  # permanent, contract, part_time
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(20))
    bank_details = Column(JSON, default={})
    certifications = Column(JSON, default={})
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    school: "School" = relationship("School", back_populates="teachers")
    user: "User" = relationship("User")
    department: "Department" = relationship("Department", foreign_keys=[department_id], back_populates="teachers")
    assignments: "List['TeacherAssignment']" = relationship("TeacherAssignment", back_populates="teacher")
    attendance_records: "List['TeacherAttendance']" = relationship("TeacherAttendance", back_populates="teacher")
    timetable_entries: "List['TimetableEntry']" = relationship("TimetableEntry", back_populates="teacher")

class TeacherAssignment(TenantBaseModel):
    __tablename__ = "teacher_assignments"
    
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"), nullable=False)
    is_class_teacher = Column(Boolean, default=False)
    assignment_date = Column(Date)
    
    # Relationships
    teacher: "Teacher" = relationship("Teacher", back_populates="assignments")
    subject: "Subject" = relationship("Subject")
    class_assigned: "Class" = relationship("Class")
    academic_session: "AcademicSession" = relationship("AcademicSession")
