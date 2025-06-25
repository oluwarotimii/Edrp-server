from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database import get_db
from models.user import User, UserRole
from models.email_template import EmailTemplate, SentEmail, EmailTemplateType
from schemas.email_template import (
    EmailTemplateCreate, 
    EmailTemplateUpdate, 
    EmailTemplateResponse,
    EmailTemplateListResponse,
    EmailPreviewRequest,
    EmailPreviewResponse,
    TestEmailRequest,
    CustomEmailRequest,
    SentEmailResponse
)
from services.email_service import EmailService
from .dependencies import require_permission, get_current_user

router = APIRouter(prefix="/admin/email-templates", tags=["Admin - Email Templates"])

# Helper function to convert DB model to response model
def template_to_response(template: EmailTemplate) -> EmailTemplateResponse:
    return EmailTemplateResponse(
        id=template.id,
        name=template.name,
        subject=template.subject,
        body=template.body,
        template_type=template.template_type,
        variables=template.variables or {},
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
        created_by=template.created_by,
        available_variables=template.get_available_variables()
    )

@router.post("/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    template_data: EmailTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new email template
    """
    require_permission("email_templates:create")(current_user)
    
    # Check if template with same name exists
    existing = db.query(EmailTemplate).filter(
        EmailTemplate.name == template_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template with this name already exists"
        )
    
    # Create new template
    template = EmailTemplate(
        id=f"tpl_{uuid.uuid4().hex[:16]}",
        **template_data.dict(),
        created_by=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template_to_response(template)

@router.get("/", response_model=EmailTemplateListResponse)
async def list_email_templates(
    skip: int = 0,
    limit: int = 100,
    template_type: Optional[EmailTemplateType] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all email templates with optional filtering
    """
    require_permission("email_templates:read")(current_user)
    
    query = db.query(EmailTemplate)
    
    # Apply filters
    if template_type:
        query = query.filter(EmailTemplate.template_type == template_type)
    if is_active is not None:
        query = query.filter(EmailTemplate.is_active == is_active)
    if search:
        query = query.filter(
            (EmailTemplate.name.ilike(f"%{search}%")) |
            (EmailTemplate.subject.ilike(f"%{search}%"))
        )
    
    # Get total count and paginated results
    total = query.count()
    templates = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [template_to_response(t) for t in templates]
    }

@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get email template by ID
    """
    require_permission("email_templates:read")(current_user)
    
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template_to_response(template)

@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: str,
    template_data: EmailTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing email template
    """
    require_permission("email_templates:update")(current_user)
    
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Update fields
    update_data = template_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(template)
    
    return template_to_response(template)

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an email template (soft delete)
    """
    require_permission("email_templates:delete")(current_user)
    
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Soft delete
    template.is_active = False
    db.commit()
    
    return None

@router.post("/preview", response_model=EmailPreviewResponse)
async def preview_email_template(
    preview_data: EmailPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Preview how an email template will look with the given variables
    """
    require_permission("email_templates:read")(current_user)
    
    email_service = EmailService(db)
    try:
        rendered = await email_service.render_template(
            preview_data.template_id,
            preview_data.variables or {}
        )
        return rendered
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/test", status_code=status.HTTP_200_OK)
async def send_test_email(
    test_data: TestEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a test email with the given template and variables
    """
    require_permission("email_templates:test")(current_user)
    
    email_service = EmailService(db)
    try:
        result = await email_service.send_templated_email(
            template_id=test_data.template_id,
            to_emails=test_data.recipient_email,
            variables=test_data.variables or {},
            background_tasks=background_tasks
        )
        return {"message": "Test email sent successfully", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/send-custom", status_code=status.HTTP_200_OK)
async def send_custom_email(
    email_data: CustomEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a custom email (not using a template)
    """
    require_permission("email_templates:send_custom")(current_user)
    
    email_service = EmailService(db)
    try:
        result = await email_service.send_custom_email(
            to_emails=email_data.recipient_emails,
            subject=email_data.subject,
            body=email_data.body,
            cc=email_data.cc,
            bcc=email_data.bcc,
            reply_to=email_data.reply_to,
            attachments=email_data.attachments,
            background_tasks=background_tasks
        )
        return {"message": "Custom email sent successfully", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/sent-emails/", response_model=List[SentEmailResponse])
async def list_sent_emails(
    skip: int = 0,
    limit: int = 50,
    template_id: Optional[str] = None,
    status: Optional[str] = None,
    recipient_email: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List sent emails with filtering options
    """
    require_permission("email_templates:view_sent")(current_user)
    
    query = db.query(SentEmail)
    
    # Apply filters
    if template_id:
        query = query.filter(SentEmail.template_id == template_id)
    if status:
        query = query.filter(SentEmail.status == status)
    if recipient_email:
        query = query.filter(SentEmail.recipient_email.ilike(f"%{recipient_email}%"))
    if date_from:
        query = query.filter(SentEmail.sent_at >= date_from)
    if date_to:
        # Add one day to include the entire end date
        query = query.filter(SentEmail.sent_at < date_to.replace(hour=23, minute=59, second=59))
    
    # Order by sent_at descending (newest first)
    query = query.order_by(SentEmail.sent_at.desc())
    
    # Apply pagination
    emails = query.offset(skip).limit(limit).all()
    
    return emails

@router.get("/sent-emails/{email_id}", response_model=SentEmailResponse)
async def get_sent_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a sent email
    """
    require_permission("email_templates:view_sent")(current_user)
    
    email = db.query(SentEmail).filter(SentEmail.id == email_id).first()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    return email
