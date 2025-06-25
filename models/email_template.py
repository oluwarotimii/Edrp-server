from sqlalchemy import Column, String, Text, Boolean, DateTime, func, Enum
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
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    template_type = Column(Enum(EmailTemplateType), default=EmailTemplateType.CUSTOM)
    variables = Column(JSONB, default=dict)  # Available variables for this template
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(50))  # User ID who created the template
    
    # Relationships
    sent_emails = relationship("SentEmail", back_populates="template")
    
    def get_available_variables(self) -> dict:
        """Return available variables for this template"""
        default_vars = {
            "school_name": "Name of the school",
            "user_name": "Name of the user",
            "user_email": "Email of the user",
            "support_email": "Support email address",
            "support_phone": "Support phone number",
            "current_date": "Current date",
            "current_year": "Current year"
        }
        
        # Add template-specific variables
        if self.template_type == EmailTemplateType.TRIAL_STARTED:
            default_vars.update({
                "trial_days": "Number of trial days",
                "trial_end_date": "Trial end date"
            })
        elif self.template_type == EmailTemplateType.TRIAL_ENDING_SOON:
            default_vars.update({
                "days_left": "Days left in trial",
                "trial_end_date": "Trial end date"
            })
        elif self.template_type == EmailTemplateType.SUBSCRIPTION_CONFIRMATION:
            default_vars.update({
                "plan_name": "Name of the subscription plan",
                "amount": "Subscription amount",
                "billing_cycle": "Billing cycle (monthly/yearly)",
                "next_billing_date": "Next billing date",
                "subscription_id": "Subscription ID"
            })
        elif self.template_type == EmailTemplateType.PAYMENT_FAILED:
            default_vars.update({
                "plan_name": "Name of the subscription plan",
                "retry_date": "Retry date for payment",
                "amount_due": "Amount due",
                "payment_method": "Last used payment method"
            })
            
        return {**default_vars, **(self.variables or {})}

class SentEmail(Base):
    __tablename__ = "sent_emails"
    
    id = Column(String(50), primary_key=True, index=True)
    template_id = Column(String(50), index=True)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), default="sent")  # sent, delivered, failed, bounced
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)  # Additional metadata
    
    # Relationships
    template = relationship("EmailTemplate", back_populates="sent_emails")
