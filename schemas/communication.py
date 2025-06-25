from pydantic import BaseModel, field_validator
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Enums for Communication Schemas ---
class MessageTypeEnum(str, Enum):
    DIRECT = "Direct"
    BROADCAST = "Broadcast"

class MessagePriorityEnum(str, Enum):
    NORMAL = "Normal"
    HIGH = "High"
    LOW = "Low"

class BehaviorSeverityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class BehaviorStatusEnum(str, Enum):
    OPEN = "Open"
    INVESTIGATING = "Investigating"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class MessageBase(BaseModel):
    recipient_id: int
    subject: str
    content: str
    message_type: MessageTypeEnum = MessageTypeEnum.DIRECT
    priority: MessagePriorityEnum = MessagePriorityEnum.NORMAL
    parent_message_id: Optional[int] = None

    @field_validator('message_type', 'priority', mode='before')
    @classmethod
    def title_case_fields(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    is_read: Optional[bool] = None

class Message(MessageBase):
    id: int
    sender_id: int
    school_id: int
    is_read: bool = False
    read_at: Optional[datetime] = None
    attachments: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class BehaviorReportBase(BaseModel):
    student_id: int
    incident_date: datetime
    incident_type: str
    severity: BehaviorSeverityEnum

    @field_validator('incident_type', 'severity', mode='before')
    @classmethod
    def title_case_fields(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
    title: str
    description: str
    location: Optional[str] = None
    witnesses: Optional[str] = None
    action_taken: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None

class BehaviorReportCreate(BehaviorReportBase):
    pass

class BehaviorReportUpdate(BaseModel):
    incident_type: Optional[str] = None
    severity: Optional[BehaviorSeverityEnum] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    witnesses: Optional[str] = None
    action_taken: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    parent_notified: Optional[bool] = None
    parent_notification_date: Optional[datetime] = None
    status: Optional[BehaviorStatusEnum] = None

    @field_validator('incident_type', 'severity', 'status', mode='before')
    @classmethod
    def title_case_fields(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v

class BehaviorReport(BehaviorReportBase):
    id: int
    reported_by: int
    school_id: int
    parent_notified: bool = False
    parent_notification_date: Optional[datetime] = None
    status: BehaviorStatusEnum = BehaviorStatusEnum.OPEN

    @field_validator('status', mode='before')
    @classmethod
    def title_case_status(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class HappeningBase(BaseModel):
    title: str
    description: str
    category: str
    target_audience: Optional[str] = None

    @field_validator('category', 'target_audience', mode='before')
    @classmethod
    def title_case_fields(cls, v: str) -> str:
        if isinstance(v, str):
            return v.title()
        return v
    event_date: Optional[datetime] = None
    location: Optional[str] = None

class HappeningCreate(HappeningBase):
    pass

class HappeningUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    target_audience: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    is_published: Optional[bool] = None
    attachments: Optional[Dict[str, Any]] = None

class Happening(HappeningBase):
    id: int
    school_id: int
    is_published: bool = False
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None
    attachments: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class UnreadMessageCount(BaseModel):
    count: int
