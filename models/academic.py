from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship, Mapped
from .base import TenantBaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .school import School
    from .teacher import Teacher
    from .student import Student
    from .timetable import TimetableEntry
    from .assessment import Assessment

class Department(TenantBaseModel):
    __tablename__ = "departments"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    head_teacher_id = Column(Integer, ForeignKey("teachers.id"))
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="departments")
    head_teacher: Mapped["Teacher"] = relationship("Teacher", foreign_keys=[head_teacher_id], post_update=True)
    teachers: Mapped[List["Teacher"]] = relationship("Teacher", foreign_keys="Teacher.department_id", back_populates="department")
    subjects: Mapped[List["Subject"]] = relationship("Subject", back_populates="department")

class Class(TenantBaseModel):
    __tablename__ = "classes"
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    class_teacher_id = Column(Integer, ForeignKey("teachers.id"))
    capacity = Column(Integer)
    room_number = Column(String(20))
    grade_level = Column(Integer)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    class_teacher: Mapped["Teacher"] = relationship("Teacher", foreign_keys=[class_teacher_id], post_update=True)
    students: Mapped[List["Student"]] = relationship("Student", back_populates="class_assigned")
    subjects: Mapped[List["Subject"]] = relationship("Subject", secondary="class_subjects", back_populates="classes")
    timetable_entries: Mapped[List["TimetableEntry"]] = relationship("TimetableEntry", back_populates="class_assigned")

class Subject(TenantBaseModel):
    __tablename__ = "subjects"
    
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True)
    description = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.id"))
    is_core = Column(Boolean, default=False)
    credit_units = Column(Integer, default=1)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="subjects")
    classes: Mapped[List["Class"]] = relationship("Class", secondary="class_subjects", back_populates="subjects")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="subject")

# Association table for many-to-many relationship between classes and subjects
from sqlalchemy import Table
class_subjects = Table(
    'class_subjects',
    TenantBaseModel.metadata,
    Column('class_id', Integer, ForeignKey('classes.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),
    Column('school_id', Integer, nullable=False)
)

class AcademicSession(TenantBaseModel):
    __tablename__ = "academic_sessions"
    
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    terms: Mapped[List["Term"]] = relationship("Term", back_populates="academic_session")

class Term(TenantBaseModel):
    __tablename__ = "terms"
    
    name = Column(String(100), nullable=False)
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    academic_session: Mapped["AcademicSession"] = relationship("AcademicSession", back_populates="terms")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="term")
