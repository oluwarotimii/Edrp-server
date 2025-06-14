from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Float, JSON
from sqlalchemy.orm import relationship, Mapped
from .base import TenantBaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .academic import Subject, Class, Term
    from .student import Student
    from .user import User

class AssessmentScheme(TenantBaseModel):
    __tablename__ = "assessment_schemes"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    components: Mapped[List["AssessmentComponent"]] = relationship("AssessmentComponent", back_populates="scheme")

class AssessmentComponent(TenantBaseModel):
    __tablename__ = "assessment_components"
    
    scheme_id = Column(Integer, ForeignKey("assessment_schemes.id"), nullable=False)
    name = Column(String(100), nullable=False)  # CA, Exam, Practical, etc.
    weight_percentage = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    scheme: Mapped["AssessmentScheme"] = relationship("AssessmentScheme", back_populates="components")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="component")

class GradingScale(TenantBaseModel):
    __tablename__ = "grading_scales"
    
    grade = Column(String(5), nullable=False)  # A, B, C, D, F
    min_score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    description = Column(String(100))
    gpa_value = Column(Float)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)

class Assessment(TenantBaseModel):
    __tablename__ = "assessments"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    term_id = Column(Integer, ForeignKey("terms.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("assessment_components.id"), nullable=False)
    max_score = Column(Float, nullable=False)
    date_conducted = Column(Date)
    is_published = Column(Boolean, default=False)
    instructions = Column(Text)
    duration_minutes = Column(Integer)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="assessments")
    class_assigned: Mapped["Class"] = relationship("Class")
    term: Mapped["Term"] = relationship("Term", back_populates="assessments")
    component: Mapped["AssessmentComponent"] = relationship("AssessmentComponent", back_populates="assessments")
    scores: Mapped[List["Score"]] = relationship("Score", back_populates="assessment")

class Score(TenantBaseModel):
    __tablename__ = "scores"
    
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    score = Column(Float, nullable=False)
    remarks = Column(Text)
    recorded_by = Column(Integer, ForeignKey("users.id"))
    recorded_at = Column(DateTime)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="scores")
    student: Mapped["Student"] = relationship("Student", back_populates="scores")
    recorder: Mapped["User"] = relationship("User")
