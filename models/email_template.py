from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Enum, Boolean, UniqueConstraint
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from enum import Enum as PyEnum

class EmailTemplateType(str, PyEnum):
    TRIAL_STARTED = "trial_started"
    TRIAL_ENDING_SOON = "trial_ending_soon"
    SUBSCRIPTION_CONFIRMATION = "subscription_confirmation"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_RECEIVED = "payment_received"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PASSWORD_RESET = "password_reset"
    WELCOME_EMAIL = "welcome_email"
    CUSTOM = "custom"

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(String(50), primary_key=True, index=True)  # Using string ID for better readability
    name = Column(String(100), nullable=False)
    subject = Column(String(255), nullable=False) # Default subject
    subject_translations = Column(JSONB, default=dict) # New: Subject translations
    body = Column(Text, nullable=False) # Default body
    body_translations = Column(JSONB, default=dict) # New: Body translations
    template_type = Column(Enum(EmailTemplateType), default=EmailTemplateType.CUSTOM)
    variables = Column(JSONB, default=dict)  # Available variables for this template
    predefined_attachments = Column(JSONB, default=list) # New: Predefined attachments
    category = Column(String(100), nullable=True) # New: Category for templates
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1, nullable=False) # New: Version number
    parent_template_id = Column(String(50), ForeignKey("email_templates.id"), nullable=True) # New: Link to original template
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(50))  # User ID who created the template
    
    # Relationships
    sent_emails = relationship("SentEmail", back_populates="template")
    # New relationship for versions
    versions = relationship("EmailTemplate", backref="parent_template", remote_side=[id])
    
    def get_available_variables(self, db: Session) -> dict:
        """Return available variables for this template by fetching from definitions."""
        # Fetch common variables
        common_vars = db.query(EmailTemplateVariableDefinition).filter(
            EmailTemplateVariableDefinition.template_type == None # Common variables
        ).all()

        # Fetch template-specific variables
        template_specific_vars = db.query(EmailTemplateVariableDefinition).filter(
            EmailTemplateVariableDefinition.template_type == self.template_type
        ).all()

        all_vars = {}
        for var_def in common_vars + template_specific_vars:
            all_vars[var_def.variable_name] = var_def.description

        return {**all_vars, **(self.variables or {})}

class SentEmail(Base):
    __tablename__ = "sent_emails"

    id = Column(String(50), primary_key=True, index=True)
    template_id = Column(String(50), ForeignKey("email_templates.id"), index=True)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="sent")  # sent, delivered, failed, bounced, opened, clicked, complained
    delivery_status_code = Column(String(100), nullable=True) # New: More granular status code from ESP
    delivery_details = Column(JSONB, default=dict) # New: Raw webhook payload or specific details
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True) # New: Timestamp for email open
    clicked_at = Column(DateTime(timezone=True), nullable=True) # New: Timestamp for link click
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)  # Additional metadata

    # Relationships
    template = relationship("EmailTemplate", back_populates="sent_emails")

class EmailTemplateVariableDefinition(Base):
    __tablename__ = "email_template_variable_definitions"

    id = Column(Integer, primary_key=True, index=True)
    template_type = Column(Enum(EmailTemplateType), nullable=False)
    variable_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False)
    default_value = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint('template_type', 'variable_name', name='_template_type_variable_uc'),)
