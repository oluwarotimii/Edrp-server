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
    subject_translations: Optional[Dict[str, str]] = Field(default_factory=dict)
    body: str
    body_translations: Optional[Dict[str, str]] = Field(default_factory=dict)
    template_type: EmailTemplateType = EmailTemplateType.CUSTOM
    variables: Dict[str, str] = Field(default_factory=dict)
    predefined_attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    category: Optional[str] = None # New
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
    subject_translations: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    body_translations: Optional[Dict[str, str]] = None
    template_type: Optional[EmailTemplateType] = None
    variables: Optional[Dict[str, str]] = None
    predefined_attachments: Optional[List[Dict[str, Any]]] = None
    category: Optional[str] = None # New
    is_active: Optional[bool] = None

# For response
class EmailTemplateResponse(EmailTemplateBase):
    id: str
    version: int
    parent_template_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    available_variables: Dict[str, str] = {}
    subject_translations: Dict[str, str] = Field(default_factory=dict)
    body_translations: Dict[str, str] = Field(default_factory=dict)
    predefined_attachments: List[Dict[str, Any]] = Field(default_factory=list)
    category: Optional[str] = None # New

    class Config:
        orm_mode = True

class EmailTemplateVersion(BaseModel):
    id: str
    name: str
    version: int
    created_at: datetime
    created_by: Optional[str] = None

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
    delivery_status_code: Optional[str] = None # New
    delivery_details: Dict[str, Any] = Field(default_factory=dict) # New
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None # New
    clicked_at: Optional[datetime] = None # New
    error_message: Optional[str] = None

    class Config:
        orm_mode = True

class EmailTemplateVariableDefinitionBase(BaseModel):
    template_type: EmailTemplateType
    variable_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_required: bool = False
    default_value: Optional[str] = None

class EmailTemplateVariableDefinitionCreate(EmailTemplateVariableDefinitionBase):
    pass

class EmailTemplateVariableDefinitionUpdate(BaseModel):
    description: Optional[str] = None
    is_required: Optional[bool] = None
    default_value: Optional[str] = None

class EmailTemplateVariableDefinitionResponse(EmailTemplateVariableDefinitionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True