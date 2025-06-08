from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from .base import TenantBaseModel

class Department(TenantBaseModel):
    __tablename__ = "departments"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    head_teacher_id = Column(Integer, ForeignKey("teachers.id"))
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    school = relationship("School", back_populates="departments")
    teachers = relationship("Teacher", back_populates="department")
    subjects = relationship("Subject", back_populates="department")

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
    students = relationship("Student", back_populates="class_assigned")
    subjects = relationship("Subject", secondary="class_subjects", back_populates="classes")
    timetable_entries = relationship("TimetableEntry", back_populates="class_assigned")

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
    department = relationship("Department", back_populates="subjects")
    classes = relationship("Class", secondary="class_subjects", back_populates="subjects")
    assessments = relationship("Assessment", back_populates="subject")

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
    terms = relationship("Term", back_populates="academic_session")

class Term(TenantBaseModel):
    __tablename__ = "terms"
    
    name = Column(String(100), nullable=False)
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    academic_session = relationship("AcademicSession", back_populates="terms")
    assessments = relationship("Assessment", back_populates="term")
