from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime, date
import os
import uuid

from database import get_db
from models.admission import AdmissionApplication, ApplicationDocument, AdmissionFormTemplate
from models.user import User, ProspectiveApplicant
from models.student import Student # Added for approve_application
from schemas.admission import (
    AdmissionApplication as AdmissionApplicationSchema, AdmissionApplicationCreate, AdmissionApplicationUpdate,
    ApplicationDocument as ApplicationDocumentSchema, ApplicationDocumentCreate,
    ApplicationStatusUpdate, ApplicationApproval,
    AdmissionFormTemplate as AdmissionFormTemplateSchema, AdmissionFormTemplateCreate, AdmissionFormTemplateUpdate,
    PublicApplicationStatus
)
from schemas.prospective_applicant import (
    ProspectiveApplicantCreate, ProspectiveApplicantLogin, ProspectiveApplicantResponse, ProspectiveApplicantToken
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException
from config import settings
from models.school import SchoolSubscription
from schemas.subscription import SubscriptionStatusEnum
from utils.storage import get_school_storage_usage
from services.auth import get_password_hash, verify_password, create_access_token
from services.email_service import EmailService

router = APIRouter()

# --- Prospective Applicant Endpoints ---

@router.post("/admissions/register-applicant", response_model=ProspectiveApplicantResponse, status_code=status.HTTP_201_CREATED)
async def register_prospective_applicant(
    applicant_data: ProspectiveApplicantCreate,
    db: Session = Depends(get_db)
):
    """Register a new prospective applicant."""
    existing_applicant = db.query(ProspectiveApplicant).filter(
        ProspectiveApplicant.email == applicant_data.email
    ).first()
    if existing_applicant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    hashed_password = get_password_hash(applicant_data.password)
    db_applicant = ProspectiveApplicant(
        email=applicant_data.email,
        hashed_password=hashed_password,
        first_name=applicant_data.first_name,
        last_name=applicant_data.last_name,
        phone=applicant_data.phone,
        school_id=applicant_data.school_id,
        is_verified=False,
        verification_token=str(uuid.uuid4())
    )
    db.add(db_applicant)
    db.commit()
    db.refresh(db_applicant)

    email_service = EmailService(db)
    verification_link = f"http://your-frontend-domain/verify-applicant?token={db_applicant.verification_token}"
    await email_service.send_custom_email(
        to_emails=[db_applicant.email],
        subject="Verify Your Applicant Account",
        body=f"Please click on the link to verify your account: {verification_link}"
    )

    return db_applicant

@router.post("/admissions/applicant-login", response_model=ProspectiveApplicantToken)
async def login_prospective_applicant(
    applicant_data: ProspectiveApplicantLogin,
    db: Session = Depends(get_db)
):
    """Login a prospective applicant and return an access token."""
    applicant = db.query(ProspectiveApplicant).filter(
        ProspectiveApplicant.email == applicant_data.email
    ).first()

    if not applicant or not verify_password(applicant_data.password, applicant.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not applicant.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please check your email for verification link."
        )

    access_token = create_access_token(data={"sub": applicant.email, "school_id": applicant.school_id, "type": "prospective_applicant"})
    return {"access_token": access_token, "token_type": "bearer", "applicant": applicant}

@router.get("/admissions/verify-applicant", response_model=dict)
async def verify_applicant_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify prospective applicant's email using a token."""
    applicant = db.query(ProspectiveApplicant).filter(
        ProspectiveApplicant.verification_token == token
    ).first()

    if not applicant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token."
        )

    applicant.is_verified = True
    applicant.verification_token = None
    db.commit()
    db.refresh(applicant)

    return {"message": "Email verified successfully. You can now log in."}

# --- Admission Form Template Endpoints ---

@router.post("/admission-form-templates", response_model=AdmissionFormTemplateSchema, status_code=status.HTTP_201_CREATED)
def create_admission_form_template(
    template: AdmissionFormTemplateCreate,
    db: Session = Depends(get_db),
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user),
    school_id: int = Depends(get_current_school) # This will be the school_id of the current_user
):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authenticated users can manage form templates.")

    if template.is_default:
        # Only super admins can create default templates
        if "super_admin" not in [role.name for role in current_user.roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admins can create default form templates.")
        # Default templates are not tied to a specific school_id
        db_template = AdmissionFormTemplate(**template.dict(exclude_unset=True), school_id=None)
    else:
        # Regular templates are tied to the current user's school
        require_permission("admissions:manage_forms")(current_user)
        db_template = AdmissionFormTemplate(**template.dict(exclude_unset=True), school_id=school_id)

    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/admission-form-templates", response_model=List[AdmissionFormTemplateSchema])
def get_admission_form_templates(
    db: Session = Depends(get_db),
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    is_default: Optional[bool] = Query(None, description="Filter by default templates")
):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authenticated users can view form templates.")

    query = db.query(AdmissionFormTemplate)

    if "super_admin" in [role.name for role in current_user.roles]:
        # Super admins can see all templates, optionally filtered by is_default
        if is_default is not None:
            query = query.filter(AdmissionFormTemplate.is_default == is_default)
    else:
        # School admins can see their own templates and default templates
        require_permission("admissions:view_forms")(current_user)
        query = query.filter(
            (AdmissionFormTemplate.school_id == school_id) | (AdmissionFormTemplate.is_default == True)
        )
        if is_default is not None:
            # If they specifically ask for default, only show default
            # If they specifically ask for non-default, only show their own
            query = query.filter(AdmissionFormTemplate.is_default == is_default)

    templates = query.all()
    return templates

@router.get("/admission-form-templates/{template_id}", response_model=AdmissionFormTemplateSchema)
def get_admission_form_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user),
    school_id: int = Depends(get_current_school)
):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authenticated users can view form templates.")

    template = db.query(AdmissionFormTemplate).filter(AdmissionFormTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Check permissions:
    # Super admin can view any template
    # School admin can view their own templates or default templates
    if "super_admin" not in [role.name for role in current_user.roles]:
        if template.is_default:
            require_permission("admissions:view_forms")(current_user)
        elif template.school_id != school_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this template.")
        else:
            require_permission("admissions:view_forms")(current_user)

    return template

@router.put("/admission-form-templates/{template_id}", response_model=AdmissionFormTemplateSchema)
def update_admission_form_template(
    template_id: int,
    template_update: AdmissionFormTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user),
    school_id: int = Depends(get_current_school)
):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authenticated users can manage form templates.")

    db_template = db.query(AdmissionFormTemplate).filter(AdmissionFormTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Permission check for updating:
    # Super admin can update any template
    # School admin can only update their own templates (not default ones)
    if "super_admin" not in [role.name for role in current_user.roles]:
        if db_template.is_default:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Default templates cannot be updated by school admins.")
        elif db_template.school_id != school_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this template.")
        else:
            require_permission("admissions:manage_forms")(current_user)

    # If trying to change is_default, only super admin can do it
    if template_update.is_default is not None and template_update.is_default != db_template.is_default:
        if "super_admin" not in [role.name for role in current_user.roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admins can change the 'is_default' status of a template.")
        # If super admin is changing to non-default, they must provide a school_id
        if not template_update.is_default and template_update.school_id is None:
             raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="School ID is required when setting a template to non-default.")


    update_data = template_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_template, key, value)

    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/admission-form-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admission_form_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user),
    school_id: int = Depends(get_current_school)
):
    if not isinstance(current_user, User):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authenticated users can manage form templates.")

    db_template = db.query(AdmissionFormTemplate).filter(AdmissionFormTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Permission check for deleting:
    # Super admin can delete any template
    # School admin can only delete their own templates (not default ones)
    if "super_admin" not in [role.name for role in current_user.roles]:
        if db_template.is_default:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Default templates cannot be deleted by school admins.")
        elif db_template.school_id != school_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this template.")
        else:
            require_permission("admissions:manage_forms")(current_user)

    db.delete(db_template)
    db.commit()
    return

# --- Admission Application Endpoints ---

@router.post("/admissions/applications", response_model=AdmissionApplicationSchema)
async def submit_application(
    application: AdmissionApplicationCreate,
    db: Session = Depends(get_db),
    school_id: int = Depends(get_current_school),
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user)
):
    # Ensure only prospective applicants can submit applications this way
    if not isinstance(current_user, ProspectiveApplicant):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only prospective applicants can submit applications."
        )

    # Ensure the prospective_applicant_id matches the authenticated user
    if application.prospective_applicant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit applications for your own account."
        )
    # 1. Fetch the form template
    template = db.query(AdmissionFormTemplate).filter(
        AdmissionFormTemplate.id == application.admission_form_template_id,
        AdmissionFormTemplate.school_id == school_id
    ).first()

    if not template or not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission form template not found or is not active"
        )

    # 2. Validate the submitted data against the template's structure
    form_structure = {field['field_name']: field for field in template.form_structure}
    submitted_data = application.form_data

    for field_name, field_definition in form_structure.items():
        if field_definition.get('required') and field_name not in submitted_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required field: {field_definition.get('label')}"
            )

        if 'min_length' in field_definition and field_name in submitted_data:
            if len(submitted_data[field_name]) < field_definition['min_length']:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Field '{field_definition.get('label')}' must be at least {field_definition['min_length']} characters long"
                )

        if field_definition.get('type') == 'select' and field_name in submitted_data:
            if submitted_data[field_name] not in field_definition.get('options', []):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid option for '{field_definition.get('label')}'"
                )

    # 3. Save the application
    db_application = AdmissionApplication(
        **application.dict(),
        school_id=school_id,
        submission_date=datetime.utcnow()
    )
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    
    return db_application

@router.get("/admissions/applications", response_model=List[AdmissionApplicationSchema])
async def get_applications(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    require_permission("admissions:view")(current_user)
    
    query = db.query(AdmissionApplication).filter(AdmissionApplication.school_id == school_id)
    
    if status:
        query = query.filter(AdmissionApplication.status == status)
    
    applications = query.order_by(AdmissionApplication.submission_date.desc()).offset(skip).limit(limit).all()
    return applications

@router.get("/admissions/applications/{application_id}", response_model=AdmissionApplicationSchema)
async def get_application(
    application_id: int,
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    application = db.query(AdmissionApplication).filter(
        AdmissionApplication.id == application_id,
        AdmissionApplication.school_id == school_id
    ).first()
    
    if not application:
        raise NotFoundException("Application not found")
    
    # Allow prospective applicants to view their own applications
    if isinstance(current_user, ProspectiveApplicant):
        if application.prospective_applicant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this application."
            )
    else:
        # For regular users, require specific permission
        require_permission("admissions:view")(current_user)
    
    return application

@router.post("/admissions/applications/{application_id}/approve", response_model=dict)
async def approve_application(
    application_id: int,
    approval: ApplicationApproval,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Approve application and create student record"""
    require_permission("admissions:approve")(current_user)
    
    application = db.query(AdmissionApplication).filter(
        AdmissionApplication.id == application_id,
        AdmissionApplication.school_id == school_id
    ).first()
    
    if not application:
        raise NotFoundException("Application not found")
    
    if application.status != "under_review":
        raise ValidationException("Application must be under review to approve")
    
    # Update application status
    application.status = "accepted"
    application.review_date = datetime.utcnow()
    application.reviewed_by = current_user.id
    
    student_record = None
    
    if approval.create_student_record:
        from services.auth import get_password_hash
        import secrets
        
        form_data = application.form_data
        
        # Generate username and temporary password
        username = f"{form_data.get('first_name', '').lower()}.{form_data.get('last_name', '').lower()}.{application.id}"
        temp_password = secrets.token_urlsafe(8)
        
        # Create user
        db_user = User(
            email=form_data.get('email') or f"{username}@{school_id}.temp.edu",
            username=username,
            first_name=form_data.get('first_name'),
            last_name=form_data.get('last_name'),
            middle_name=form_data.get('middle_name'),
            phone=form_data.get('phone'),
            address=form_data.get('address'),
            date_of_birth=form_data.get('date_of_birth'),
            gender=form_data.get('gender'),
            hashed_password=get_password_hash(temp_password),
            school_id=school_id,
            is_approved=True,
            is_verified=True
        )
        
        db.add(db_user)
        db.flush()  # Get the user ID
        
        # Create student record
        student_id = approval.student_id or f"STU-{school_id}-{db_user.id}"
        
        db_student = Student(
            user_id=db_user.id,
            student_id=student_id,
            class_id=approval.class_id or form_data.get('class_applying_for'),
            admission_date=approval.admission_date or date.today(),
            medical_info={"conditions": form_data.get('medical_conditions'), "special_needs": form_data.get('special_needs')},
            school_id=school_id
        )
        
        db.add(db_student)
        db.flush()
        
        # Create parent user if needed
        parent_username = f"parent.{form_data.get('parent_first_name', '').lower()}.{form_data.get('parent_last_name', '').lower()}.{db_student.id}"
        parent_temp_password = secrets.token_urlsafe(8)
        
        db_parent = User(
            email=form_data.get('parent_email'),
            username=parent_username,
            first_name=form_data.get('parent_first_name'),
            last_name=form_data.get('parent_last_name'),
            phone=form_data.get('parent_phone'),
            address=form_data.get('parent_address'),
            hashed_password=get_password_hash(parent_temp_password),
            school_id=school_id,
            is_approved=True,
            is_verified=True
        )
        
        db.add(db_parent)
        db.flush()
        
        # Link parent to student
        from models.student import StudentParent
        db_parent_link = StudentParent(
            student_id=db_student.id,
            parent_user_id=db_parent.id,
            relationship_type=form_data.get('relationship_to_student', '').lower(),
            is_primary_contact=True,
            school_id=school_id
        )
        
        db.add(db_parent_link)
        
        student_record = {
            "student_id": db_student.id,
            "user_id": db_user.id,
            "username": username,
            "temporary_password": temp_password,
            "parent_username": parent_username,
            "parent_temporary_password": parent_temp_password
        }
    
    db.commit()
    
    result = {
        "message": "Application approved successfully",
        "application_id": application_id,
        "status": application.status
    }
    
    if student_record:
        result["student_record"] = student_record
    
    return result

@router.post("/admissions/applications/{application_id}/documents", response_model=ApplicationDocumentSchema)
async def upload_document(
    application_id: int,
    document_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Upload required documents"""
    # Verify application exists
    application = db.query(AdmissionApplication).filter(
        AdmissionApplication.id == application_id,
        AdmissionApplication.school_id == school_id
    ).first()
    
    if not application:
        raise NotFoundException("Application not found")
    
    # Validate file size against individual limit
    if file.size > settings.MAX_FILE_SIZE:
        raise ValidationException("File size exceeds maximum allowed size per file.")

    # Check school's total storage limit
    school_subscription = db.query(SchoolSubscription).filter(
        SchoolSubscription.school_id == school_id,
        SchoolSubscription.status == SubscriptionStatusEnum.ACTIVE
    ).first()

    if not school_subscription:
        raise ValidationException("School does not have an active subscription to upload documents.")

    current_storage_mb = get_school_storage_usage(school_id, db)
    if (current_storage_mb * 1024 * 1024) + file.size > (school_subscription.plan.max_storage_mb * 1024 * 1024):
        raise ValidationException(
            f"School storage limit ({school_subscription.plan.max_storage_mb}MB) reached. "
            "Please upgrade your plan to upload more documents."
        )

    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.UPLOAD_DIR, "admissions", str(application_id))
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)

    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Create document record
    db_document = ApplicationDocument(
        application_id=application_id,
        document_type=document_type,
        file_name=file.filename,
        file_path=file_path,
        file_size=file.size,
        mime_type=file.content_type,
        uploaded_at=datetime.utcnow(),
        school_id=school_id
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document

@router.get("/admissions/public-status/{application_id}", response_model=PublicApplicationStatus)
async def get_public_application_status(
    application_id: int,
    db: Session = Depends(get_db)
):
    """Get public status of an admission application by ID (no authentication required)"""
    application = db.query(AdmissionApplication).filter(
        AdmissionApplication.id == application_id
    ).first()
    
    if not application:
        raise NotFoundException("Application not found")
    
    return application