from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class EmailTemplateType(str, Enum):
    TRIAL_STARTED = "trial_started"
    TRIAL_ENDING_SOON = "trial_ending_soon"
    SUBSCRIPTION_CONFIRMATION = "subscription_confirmation"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_RECEIVED = "payment_received"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PASSWORD_RESET = "password_reset"
    WELCOME_EMAIL = "welcome_email"
    CUSTOM = "custom"

# Base schema
class EmailTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=255)
    body: str
    template_type: EmailTemplateType = EmailTemplateType.CUSTOM
    variables: Dict[str, str] = Field(default_factory=dict)
    is_active: bool = True

# For creation
class EmailTemplateCreate(EmailTemplateBase):
    pass

    @validator('body')
    def validate_template_syntax(cls, v):
        # Basic validation for template variables
        if '{{' in v and '}}' in v:
            # Add more sophisticated validation if needed
            pass
        return v

# For update
class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None
    template_type: Optional[EmailTemplateType] = None
    variables: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None

# For response
class EmailTemplateResponse(EmailTemplateBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    available_variables: Dict[str, str] = {}

    class Config:
        orm_mode = True

# For listing
class EmailTemplateListResponse(BaseModel):
    total: int
    items: List[EmailTemplateResponse]

# For previewing templates
class EmailPreviewRequest(BaseModel):
    template_id: str
    variables: Dict[str, Any] = {}

class EmailPreviewResponse(BaseModel):
    subject: str
    body: str

# For sending test emails
class TestEmailRequest(BaseModel):
    template_id: str
    recipient_email: str
    variables: Dict[str, Any] = {}

# For sending custom emails
class CustomEmailRequest(BaseModel):
    recipient_emails: List[str]
    subject: str
    body: str
    cc: List[str] = []
    bcc: List[str] = []
    reply_to: Optional[str] = None
    attachments: List[Dict[str, Any]] = []

# For sent emails
class SentEmailResponse(BaseModel):
    id: str
    template_id: str
    recipient_email: str
    subject: str
    status: str
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        orm_mode = True
