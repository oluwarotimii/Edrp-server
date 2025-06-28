from __future__ import annotations
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, JSON
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func
from .base import TenantBaseModel, Base
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User, ProspectiveApplicant
    from .school import School

class AdmissionFormTemplate(Base):
    __tablename__ = 'admission_form_templates'

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey('schools.id'), nullable=True)
    is_default = Column(Boolean, default=False)
    name = Column(String, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    form_structure = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school = relationship("School")

class AdmissionApplication(TenantBaseModel):
    __tablename__ = "admission_applications"
    
    admission_form_template_id = Column(Integer, ForeignKey('admission_form_templates.id'), nullable=False)
    prospective_applicant_id = Column(Integer, ForeignKey('prospective_applicants.id'), nullable=False)
    form_data = Column(JSON, nullable=False)
    status = Column(String(20), default="submitted")  # submitted, under_review, accepted, rejected
    submission_date = Column(DateTime)
    review_date = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    rejection_reason = Column(Text)
    notes = Column(Text)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    template = relationship("AdmissionFormTemplate")
    reviewer: Mapped["User"] = relationship("User")
    prospective_applicant: Mapped["ProspectiveApplicant"] = relationship("ProspectiveApplicant")

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
    application: Mapped["AdmissionApplication"] = relationship("AdmissionApplication")
    verifier: Mapped["User"] = relationship("User")