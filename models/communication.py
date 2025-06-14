from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .base import TenantBaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .student import Student

class Message(TenantBaseModel):
    __tablename__ = "messages"
    
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="direct")  # direct, announcement, alert
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    parent_message_id = Column(Integer, ForeignKey("messages.id"))
    attachments = Column(JSON, default={})
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    sender: "'User'" = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient: "'User'" = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
    replies: "List['Message']" = relationship("Message", remote_side=[parent_message_id])

class BehaviorReport(TenantBaseModel):
    __tablename__ = "behavior_reports"
    
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    incident_date = Column(DateTime, nullable=False)
    incident_type = Column(String(50), nullable=False)  # academic, social, disciplinary
    severity = Column(String(20), nullable=False)  # minor, major, severe
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255))
    witnesses = Column(Text)
    action_taken = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime)
    parent_notified = Column(Boolean, default=False)
    parent_notification_date = Column(DateTime)
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    student: "'Student'" = relationship("Student", back_populates="behavior_reports")
    reporter: "'User'" = relationship("User")

class Happening(TenantBaseModel):
    __tablename__ = "happenings"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # event, announcement, incident
    target_audience = Column(String(50))  # all, students, teachers, parents, staff
    event_date = Column(DateTime)
    location = Column(String(255))
    is_published = Column(Boolean, default=False)
    published_by = Column(Integer, ForeignKey("users.id"))
    published_at = Column(DateTime)
    attachments = Column(JSON, default={})
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    publisher: "'User'" = relationship("User")
