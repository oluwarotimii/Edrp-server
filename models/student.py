from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Date
from sqlalchemy.orm import relationship, Mapped
from .base import TenantBaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .school import School
    from .user import User
    from .academic import Class, Subject, AcademicSession
    from .fee import StudentFee
    from .attendance import AttendanceRecord
    from .assessment import Score
    from .communication import BehaviorReport

class Student(TenantBaseModel):
    __tablename__ = "students"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(String(50), unique=True, nullable=False)
    admission_number = Column(String(50), unique=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    admission_date = Column(Date)
    status = Column(String(20), default="active")  # active, graduated, withdrawn, suspended
    boarding_status = Column(String(20))  # boarding, day
    medical_info = Column(JSON, default={})
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relationship = Column(String(50))
    previous_school = Column(String(255))
    transfer_certificate_number = Column(String(100))
    blood_group = Column(String(5))
    allergies = Column(Text)
    medications = Column(Text)
    special_needs = Column(Text)
    graduation_date = Column(Date)
    withdrawal_date = Column(Date)
    withdrawal_reason = Column(Text)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="students")
    user: Mapped["User"] = relationship("User")
    class_assigned: Mapped["Class"] = relationship("Class", back_populates="students")
    parents: Mapped[List["StudentParent"]] = relationship("StudentParent", back_populates="student")
    custom_fields: Mapped[List["StudentCustomField"]] = relationship("StudentCustomField", back_populates="student")
    subject_enrollments: Mapped[List["StudentSubjectEnrollment"]] = relationship("StudentSubjectEnrollment", back_populates="student")
    fees: Mapped[List["StudentFee"]] = relationship("StudentFee", back_populates="student")
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="student")
    scores: Mapped[List["Score"]] = relationship("Score", back_populates="student")
    behavior_reports: Mapped[List["BehaviorReport"]] = relationship("BehaviorReport", back_populates="student")

class StudentParent(TenantBaseModel):
    __tablename__ = "student_parents"
    
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    parent_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_type = Column(String(20), nullable=False)  # father, mother, guardian
    is_primary_contact = Column(Boolean, default=False)
    can_pick_up = Column(Boolean, default=True)
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="parents")
    parent: Mapped["User"] = relationship("User")

class StudentCustomField(TenantBaseModel):
    __tablename__ = "student_custom_fields"
    
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    field_value = Column(Text)
    field_type = Column(String(20), default="text")  # text, number, date, boolean
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="custom_fields")

class StudentSubjectEnrollment(TenantBaseModel):
    __tablename__ = "student_subject_enrollments"
    
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"), nullable=False)
    enrollment_date = Column(Date)
    is_core_subject = Column(Boolean, default=False)
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="subject_enrollments")
    subject: Mapped["Subject"] = relationship("Subject")
    academic_session: Mapped["AcademicSession"] = relationship("AcademicSession")
