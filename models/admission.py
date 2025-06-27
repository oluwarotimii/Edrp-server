from __future__ import annotations
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, JSON
from sqlalchemy.orm import relationship, Mapped
from .base import TenantBaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .academic import Class, AcademicSession
    from .user import User, ProspectiveApplicant

class AdmissionApplication(TenantBaseModel):
    __tablename__ = "admission_applications"
    
    prospective_applicant_id = Column(Integer, ForeignKey("prospective_applicants.id"), nullable=True) # New field
    application_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    
    # Parent/Guardian Information
    parent_first_name = Column(String(100), nullable=False)
    parent_last_name = Column(String(100), nullable=False)
    parent_phone = Column(String(20), nullable=False)
    parent_email = Column(String(255), nullable=False)
    parent_occupation = Column(String(100))
    parent_address = Column(Text)
    relationship_to_student = Column(String(50), nullable=False)
    
    # Academic Information
    previous_school = Column(String(255))
    class_applying_for = Column(Integer, ForeignKey("classes.id"))
    academic_session_id = Column(Integer, ForeignKey("academic_sessions.id"))
    
    # Application Status
    status = Column(String(20), default="submitted")  # submitted, under_review, accepted, rejected
    submission_date = Column(DateTime)
    review_date = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    rejection_reason = Column(Text)
    notes = Column(Text)
    
    # Additional Information
    medical_conditions = Column(Text)
    special_needs = Column(Text)
    additional_info = Column(JSON, default={})
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    documents: Mapped[List["ApplicationDocument"]] = relationship("ApplicationDocument", back_populates="application")
    class_applied: Mapped["Class"] = relationship("Class")
    academic_session: Mapped["AcademicSession"] = relationship("AcademicSession")
    reviewer: Mapped["User"] = relationship("User")
    prospective_applicant: Mapped["ProspectiveApplicant"] = relationship("ProspectiveApplicant", back_populates="applications")

class ApplicationDocument(TenantBaseModel):
    __tablename__ = "application_documents"
    
    application_id = Column(Integer, ForeignKey("admission_applications.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # birth_certificate, transcript, passport, etc.
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    uploaded_at = Column(DateTime)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"))
    verified_at = Column(DateTime)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    application: Mapped["AdmissionApplication"] = relationship("AdmissionApplication", back_populates="documents")
    verifier: Mapped["User"] = relationship("User")
