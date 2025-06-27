from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

from database import get_db
from models.user import User, UserRole
from models.email_template import EmailTemplate, SentEmail, EmailTemplateType, EmailTemplateVariableDefinition
from schemas.email_template import (
    EmailTemplateCreate, 
    EmailTemplateUpdate, 
    EmailTemplateResponse,
    EmailTemplateListResponse,
    EmailPreviewRequest,
    EmailPreviewResponse,
    TestEmailRequest,
    CustomEmailRequest,
    SentEmailResponse,
    EmailTemplateVersion,
    EmailTemplateVariableDefinitionCreate,
    EmailTemplateVariableDefinitionUpdate,
    EmailTemplateVariableDefinitionResponse
)
from services.email_service import EmailService
from utils.dependencies import require_permission, get_current_user
from config import settings # Import settings for webhook secret

router = APIRouter(prefix="/admin/email-templates", tags=["Admin - Email Templates"])

# Helper function to convert DB model to response model
def template_to_response(template: EmailTemplate, db: Session) -> EmailTemplateResponse:
    return EmailTemplateResponse(
        id=template.id,
        name=template.name,
        subject=template.subject,
        body=template.body,
        template_type=template.template_type,
        variables=template.variables or {},
        is_active=template.is_active,
        version=template.version,
        parent_template_id=template.parent_template_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
        created_by=template.created_by,
        available_variables=template.get_available_variables(db)
    )

@router.post("/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_email_template(
    template_data: EmailTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new email template or a new version of an existing template.
    If a template with the same name exists, a new version is created.
    """
    require_permission("email_templates:create")(current_user)
    
    # Check if a template with the same name already exists
    existing_template = db.query(EmailTemplate).filter(
        EmailTemplate.name == template_data.name
    ).order_by(EmailTemplate.version.desc()).first()
    
    new_template_id = f"tpl_{uuid.uuid4().hex[:16]}"
    new_version = 1
    parent_id = None

    if existing_template:
        # If a template with this name exists, create a new version
        new_version = existing_template.version + 1
        parent_id = existing_template.id # Link to the previous version
        # Deactivate the previous version if it was active
        existing_template.is_active = False
        db.add(existing_template)
        db.flush()

    # Create new template (or new version)
    template = EmailTemplate(
        id=new_template_id,
        **template_data.dict(),
        version=new_version,
        parent_template_id=parent_id,
        created_by=current_user.id,
        is_active=True # New versions are active by default
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template_to_response(template, db)

@router.get("/", response_model=EmailTemplateListResponse)
async def list_email_templates(
    skip: int = 0,
    limit: int = 100,
    template_type: Optional[EmailTemplateType] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    category: Optional[str] = None, # New filter
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
    if category:
        query = query.filter(EmailTemplate.category == category)
    
    # Get total count and paginated results
    total = query.count()
    templates = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": [template_to_response(t, db) for t in templates]
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
    
    return template_to_response(template, db)

@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: str,
    template_data: EmailTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing email template by creating a new version.
    The old version will be deactivated.
    """
    require_permission("email_templates:update")(current_user)
    
    # Get the current active version of the template by its original ID (template_id)
    # We assume template_id here refers to the ID of the *current* active version
    # or the ID of the original template if we want to create a new version based on it.
    # For simplicity, let's assume template_id is the ID of the version to be updated.
    # To ensure we're always updating the latest version, we should find the latest by name.
    
    # Find the latest version of the template with the given name (if name is provided in update_data)
    # or by the template_id if it's a specific version ID.
    
    # First, find the template by the provided template_id
    existing_template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not existing_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    # Deactivate the current version
    existing_template.is_active = False
    db.add(existing_template)
    db.flush()

    # Create a new version based on the existing template's data and the update data
    new_template_id = f"tpl_{uuid.uuid4().hex[:16]}"
    new_version = existing_template.version + 1
    parent_id = existing_template.id

    # Prepare data for the new version, merging existing and updated data
    updated_fields = template_data.dict(exclude_unset=True)
    new_version_data = {
        "name": updated_fields.get("name", existing_template.name),
        "subject": updated_fields.get("subject", existing_template.subject),
        "body": updated_fields.get("body", existing_template.body),
        "template_type": updated_fields.get("template_type", existing_template.template_type),
        "variables": updated_fields.get("variables", existing_template.variables),
        "is_active": True, # New version is active
        "version": new_version,
        "parent_template_id": parent_id,
        "created_by": current_user.id, # Creator of the new version
        "updated_at": datetime.utcnow()
    }

    new_template = EmailTemplate(
        id=new_template_id,
        **new_version_data
    )
    
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    return template_to_response(new_template, db)

@router.get("/{template_name}/versions", response_model=List[EmailTemplateVersion])
async def list_template_versions(
    template_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all versions of a specific email template by name.
    """
    require_permission("email_templates:read")(current_user)

    versions = db.query(EmailTemplate).filter(
        EmailTemplate.name == template_name
    ).order_by(EmailTemplate.version.desc()).all()

    if not versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No versions found for this template name"
        )
    
    return [
        EmailTemplateVersion(
            id=v.id,
            name=v.name,
            version=v.version,
            created_at=v.created_at,
            created_by=v.created_by
        ) for v in versions
    ]

@router.post("/{template_id}/activate", response_model=EmailTemplateResponse)
async def activate_template_version(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate a specific version of an email template.
    This will deactivate all other versions of the same template name.
    """
    require_permission("email_templates:update")(current_user)

    template_to_activate = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template_to_activate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template version not found"
        )

    # Deactivate all other versions of the same template name
    db.query(EmailTemplate).filter(
        EmailTemplate.name == template_to_activate.name,
        EmailTemplate.id != template_id
    ).update({"is_active": False})

    # Activate the selected version
    template_to_activate.is_active = True
    db.commit()
    db.refresh(template_to_activate)

    return template_to_response(template_to_activate, db)

# Email Template Variable Definitions
@router.post("/variable-definitions", response_model=EmailTemplateVariableDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_variable_definition(
    variable_data: EmailTemplateVariableDefinitionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new email template variable definition.
    """
    require_permission("email_templates:manage_variables")(current_user)

    existing = db.query(EmailTemplateVariableDefinition).filter(
        EmailTemplateVariableDefinition.template_type == variable_data.template_type,
        EmailTemplateVariableDefinition.variable_name == variable_data.variable_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Variable definition for this template type and name already exists"
        )

    db_variable = EmailTemplateVariableDefinition(**variable_data.dict())
    db.add(db_variable)
    db.commit()
    db.refresh(db_variable)
    return db_variable

@router.get("/variable-definitions", response_model=List[EmailTemplateVariableDefinitionResponse])
async def list_variable_definitions(
    template_type: Optional[EmailTemplateType] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all email template variable definitions with optional filtering.
    """
    require_permission("email_templates:manage_variables")(current_user)

    query = db.query(EmailTemplateVariableDefinition)
    if template_type:
        query = query.filter(EmailTemplateVariableDefinition.template_type == template_type)

    variables = query.offset(skip).limit(limit).all()
    return variables

@router.get("/variable-definitions/{variable_id}", response_model=EmailTemplateVariableDefinitionResponse)
async def get_variable_definition(
    variable_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific email template variable definition by ID.
    """
    require_permission("email_templates:manage_variables")(current_user)

    db_variable = db.query(EmailTemplateVariableDefinition).filter(
        EmailTemplateVariableDefinition.id == variable_id
    ).first()

    if not db_variable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variable definition not found"
        )
    return db_variable

@router.put("/variable-definitions/{variable_id}", response_model=EmailTemplateVariableDefinitionResponse)
async def update_variable_definition(
    variable_id: int,
    variable_data: EmailTemplateVariableDefinitionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing email template variable definition.
    """
    require_permission("email_templates:manage_variables")(current_user)

    db_variable = db.query(EmailTemplateVariableDefinition).filter(
        EmailTemplateVariableDefinition.id == variable_id
    ).first()

    if not db_variable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variable definition not found"
        )

    for field, value in variable_data.dict(exclude_unset=True).items():
        setattr(db_variable, field, value)
    
    db.commit()
    db.refresh(db_variable)
    return db_variable

@router.delete("/variable-definitions/{variable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variable_definition(
    variable_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an email template variable definition.
    """
    require_permission("email_templates:manage_variables")(current_user)

    db_variable = db.query(EmailTemplateVariableDefinition).filter(
        EmailTemplateVariableDefinition.id == variable_id
    ).first()

    if not db_variable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variable definition not found"
        )
    
    db.delete(db_variable)
    db.commit()
    return None

    return {"message": "Webhook received and processed"}

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
