from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageBase(BaseModel):
    recipient_id: int
    subject: str
    content: str
    message_type: str = "direct"
    priority: str = "normal"
    parent_message_id: Optional[int] = None

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
    severity: str
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
    severity: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    witnesses: Optional[str] = None
    action_taken: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    parent_notified: Optional[bool] = None
    parent_notification_date: Optional[datetime] = None
    status: Optional[str] = None

class BehaviorReport(BehaviorReportBase):
    id: int
    reported_by: int
    school_id: int
    parent_notified: bool = False
    parent_notification_date: Optional[datetime] = None
    status: str = "open"
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class HappeningBase(BaseModel):
    title: str
    description: str
    category: str
    target_audience: Optional[str] = None
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
