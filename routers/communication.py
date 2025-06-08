from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.communication import Message, BehaviorReport, Happening
from models.student import Student
from models.user import User
from schemas.communication import (
    Message as MessageSchema, MessageCreate, MessageUpdate,
    BehaviorReport as BehaviorReportSchema, BehaviorReportCreate, BehaviorReportUpdate,
    Happening as HappeningSchema, HappeningCreate, HappeningUpdate,
    UnreadMessageCount
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException
from services.notifications import NotificationService

router = APIRouter()

# Message endpoints
@router.post("/messages", response_model=MessageSchema)
async def create_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new message"""
    require_permission("messages:create")(current_user)
    
    # Verify recipient exists and belongs to school
    recipient = db.query(User).filter(
        User.id == message.recipient_id,
        User.school_id == school_id
    ).first()
    
    if not recipient:
        raise NotFoundException("Recipient not found")
    
    db_message = Message(
        sender_id=current_user.id,
        recipient_id=message.recipient_id,
        subject=message.subject,
        content=message.content,
        message_type=message.message_type,
        priority=message.priority,
        parent_message_id=message.parent_message_id,
        school_id=school_id
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Send notification if high priority
    if message.priority in ["high", "urgent"]:
        notification_service = NotificationService()
        await notification_service.send_message_notification(
            recipient_id=message.recipient_id,
            sender_name=f"{current_user.first_name} {current_user.last_name}",
            subject=message.subject,
            priority=message.priority
        )
    
    return db_message

@router.get("/messages", response_model=List[MessageSchema])
async def get_messages(
    skip: int = 0,
    limit: int = 100,
    message_type: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get messages for current user"""
    query = db.query(Message).filter(
        Message.recipient_id == current_user.id,
        Message.school_id == school_id
    )
    
    if message_type:
        query = query.filter(Message.message_type == message_type)
    
    if is_read is not None:
        query = query.filter(Message.is_read == is_read)
    
    messages = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    return messages

@router.put("/messages/{message_id}/read", response_model=MessageSchema)
async def mark_message_as_read(
    message_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Mark message as read"""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.recipient_id == current_user.id,
        Message.school_id == school_id
    ).first()
    
    if not message:
        raise NotFoundException("Message not found")
    
    message.is_read = True
    message.read_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    
    return message

@router.get("/messages/unread-count", response_model=UnreadMessageCount)
async def get_unread_message_count(
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get count of unread messages"""
    count = db.query(Message).filter(
        Message.recipient_id == current_user.id,
        Message.school_id == school_id,
        Message.is_read == False
    ).count()
    
    return UnreadMessageCount(count=count)

# Behavior Report endpoints
@router.post("/behavior-reports", response_model=BehaviorReportSchema)
async def create_behavior_report(
    report: BehaviorReportCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a behavior report"""
    require_permission("behavior_reports:create")(current_user)
    
    # Verify student exists
    student = db.query(Student).filter(
        Student.id == report.student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    db_report = BehaviorReport(
        student_id=report.student_id,
        reported_by=current_user.id,
        incident_date=report.incident_date,
        incident_type=report.incident_type,
        severity=report.severity,
        title=report.title,
        description=report.description,
        location=report.location,
        witnesses=report.witnesses,
        action_taken=report.action_taken,
        follow_up_required=report.follow_up_required,
        follow_up_date=report.follow_up_date,
        school_id=school_id
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # Notify parents if severity is major or severe
    if report.severity in ["major", "severe"]:
        notification_service = NotificationService()
        await notification_service.send_behavior_report_notification(
            student_id=report.student_id,
            incident_title=report.title,
            severity=report.severity,
            db=db
        )
    
    return db_report

@router.get("/behavior-reports", response_model=List[BehaviorReportSchema])
async def get_behavior_reports(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = Query(None),
    incident_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get behavior reports"""
    require_permission("behavior_reports:view")(current_user)
    
    query = db.query(BehaviorReport).filter(BehaviorReport.school_id == school_id)
    
    if student_id:
        query = query.filter(BehaviorReport.student_id == student_id)
    if incident_type:
        query = query.filter(BehaviorReport.incident_type == incident_type)
    if severity:
        query = query.filter(BehaviorReport.severity == severity)
    if status:
        query = query.filter(BehaviorReport.status == status)
    
    reports = query.order_by(BehaviorReport.incident_date.desc()).offset(skip).limit(limit).all()
    return reports

@router.get("/behavior-reports/{report_id}", response_model=BehaviorReportSchema)
async def get_behavior_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific behavior report"""
    report = db.query(BehaviorReport).filter(
        BehaviorReport.id == report_id,
        BehaviorReport.school_id == school_id
    ).first()
    
    if not report:
        raise NotFoundException("Behavior report not found")
    
    # Check permissions - parents can view their children's reports
    if not _can_access_behavior_report(current_user, report, db):
        require_permission("behavior_reports:view")(current_user)
    
    return report

@router.put("/behavior-reports/{report_id}", response_model=BehaviorReportSchema)
async def update_behavior_report(
    report_id: int,
    report_update: BehaviorReportUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a behavior report"""
    require_permission("behavior_reports:update")(current_user)
    
    report = db.query(BehaviorReport).filter(
        BehaviorReport.id == report_id,
        BehaviorReport.school_id == school_id
    ).first()
    
    if not report:
        raise NotFoundException("Behavior report not found")
    
    # Update fields
    for field, value in report_update.dict(exclude_unset=True).items():
        setattr(report, field, value)
    
    db.commit()
    db.refresh(report)
    
    return report

def _can_access_behavior_report(current_user: User, report: BehaviorReport, db: Session) -> bool:
    """Check if current user can access behavior report"""
    # If user is the reporter
    if current_user.id == report.reported_by:
        return True
    
    # If user is a parent of the student
    from models.student import StudentParent
    parent_link = db.query(StudentParent).filter(
        StudentParent.student_id == report.student_id,
        StudentParent.parent_user_id == current_user.id
    ).first()
    
    return parent_link is not None
