from __future__ import annotations
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Float
from sqlalchemy.orm import relationship, Mapped
from .base import TenantBaseModel, BaseModel
from typing import List, TYPE_CHECKING
import sqlalchemy as sa

if TYPE_CHECKING:
    from .school import School
    from .teacher import Teacher
    from .student import Student
    from .timetable import TimetableEntry
    from .assessment import Assessment, AssessmentScheme, GradingScale
    from .academic import SubjectResult, TermResult, StudentCumulativeResult

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
    subject_results: Mapped[List["SubjectResult"]] = relationship("SubjectResult", back_populates="subject")

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
    is_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime, nullable=True)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    terms: Mapped[List["Term"]] = relationship("Term", back_populates="academic_session")
    cumulative_results: Mapped[List["StudentCumulativeResult"]] = relationship("StudentCumulativeResult", back_populates="academic_session")

class Term(TenantBaseModel):
    __tablename__ = "terms"
    
    name = Column(String(100), nullable=False)
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime, nullable=True)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    academic_session: Mapped["AcademicSession"] = relationship("AcademicSession", back_populates="terms")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="term")
    subject_results: Mapped[List["SubjectResult"]] = relationship("SubjectResult", back_populates="term")
    term_results: Mapped[List["TermResult"]] = relationship("TermResult", back_populates="term")


class SubjectResult(TenantBaseModel):
    __tablename__ = "subject_results"

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    term_id = Column(Integer, ForeignKey("terms.id"), nullable=False)
    
    total_score = Column(Float, nullable=False)
    grade = Column(String(10), nullable=False)
    gpa = Column(Float, nullable=True) # Nullable if GPA is not used by the school's profile
    rank = Column(Integer, nullable=True) # Rank within the class/subject
    remarks = Column(Text, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="subject_results")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="subject_results")
    term: Mapped["Term"] = relationship("Term", back_populates="subject_results")

    # Composite unique constraint to ensure one result per student per subject per term
    __table_args__ = (sa.UniqueConstraint('student_id', 'subject_id', 'term_id', name='_student_subject_term_uc'),)


class TermResult(TenantBaseModel):
    __tablename__ = "term_results"

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    term_id = Column(Integer, ForeignKey("terms.id"), nullable=False)
    
    total_gpa = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    overall_grade = Column(String(10), nullable=True)
    position_in_class = Column(Integer, nullable=True)
    remarks = Column(Text, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="term_results")
    term: Mapped["Term"] = relationship("Term", back_populates="term_results")

    __table_args__ = (sa.UniqueConstraint('student_id', 'term_id', name='_student_term_uc'),)


class StudentCumulativeResult(TenantBaseModel):
    __tablename__ = "student_cumulative_results"

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"), nullable=False)

    cumulative_gpa = Column(Float, nullable=True)
    cumulative_score = Column(Float, nullable=True)
    overall_cumulative_grade = Column(String(10), nullable=True)
    overall_cumulative_position = Column(Integer, nullable=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="cumulative_results")
    academic_session: Mapped["AcademicSession"] = relationship("AcademicSession", back_populates="cumulative_results")

    __table_args__ = (sa.UniqueConstraint('student_id', 'academic_session_id', name='_student_academic_session_uc'),)


class GradingProfile(BaseModel):
    __tablename__ = "grading_profiles"

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    
    # --- Super Admin Defined Rules ---
    uses_gpa = Column(Boolean, default=False, nullable=False)
    gpa_scale = Column(Float, default=4.0)
    allows_astar_grade = Column(Boolean, default=False, nullable=False)
    remarks_are_mandatory = Column(Boolean, default=False, nullable=False)

    # Relationship to schools that have adopted this profile
    schools: Mapped[List["School"]] = relationship("School", back_populates="grading_profile")
