from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os
import uuid

from database import get_db
from models.admission import AdmissionApplication, ApplicationDocument
from models.academic import Class, AcademicSession
from models.user import User, ProspectiveApplicant # Import ProspectiveApplicant
from models.student import Student
from schemas.admission import (
    AdmissionApplication as AdmissionApplicationSchema, AdmissionApplicationCreate, AdmissionApplicationUpdate,
    ApplicationDocument as ApplicationDocumentSchema, ApplicationDocumentCreate,
    ApplicationStatusUpdate, ApplicationApproval
)
from schemas.prospective_applicant import (
    ProspectiveApplicantCreate, ProspectiveApplicantLogin, ProspectiveApplicantResponse, ProspectiveApplicantToken
) # New import
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException
from config import settings
from models.school import SchoolSubscription
from schemas.subscription import SubscriptionStatusEnum
from utils.storage import get_school_storage_usage
from services.auth import get_password_hash, verify_password, create_access_token # New imports
from services.email_service import EmailService # New import for email verification

router = APIRouter()

@router.post("/admissions/register-applicant", response_model=ProspectiveApplicantResponse, status_code=status.HTTP_201_CREATED)
async def register_prospective_applicant(
    applicant_data: ProspectiveApplicantCreate,
    db: Session = Depends(get_db)
):
    """Register a new prospective applicant."""
    # Check if email already exists
    existing_applicant = db.query(ProspectiveApplicant).filter(
        ProspectiveApplicant.email == applicant_data.email
    ).first()
    if existing_applicant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Check if school exists
    school = db.query(School).filter(School.id == applicant_data.school_id).first()
    if not school:
        raise NotFoundException("School not found.")

    hashed_password = get_password_hash(applicant_data.password)
    db_applicant = ProspectiveApplicant(
        email=applicant_data.email,
        hashed_password=hashed_password,
        first_name=applicant_data.first_name,
        last_name=applicant_data.last_name,
        phone=applicant_data.phone,
        school_id=applicant_data.school_id,
        is_verified=False, # Will be verified via email
        verification_token=str(uuid.uuid4()) # Generate a verification token
    )
    db.add(db_applicant)
    db.commit()
    db.refresh(db_applicant)

    # Send verification email (placeholder)
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
    applicant.verification_token = None # Invalidate token after use
    db.commit()
    db.refresh(applicant)

    return {"message": "Email verified successfully. You can now log in."}

@router.post("/admissions/applications", response_model=AdmissionApplicationSchema)
async def submit_application(
    application: AdmissionApplicationCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Submit a new student application"""
    # Generate application number
    application_number = f"APP-{school_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    db_application = AdmissionApplication(
        application_number=application_number,
        first_name=application.first_name,
        last_name=application.last_name,
        middle_name=application.middle_name,
        date_of_birth=application.date_of_birth,
        gender=application.gender,
        address=application.address,
        phone=application.phone,
        email=application.email,
        parent_first_name=application.parent_first_name,
        parent_last_name=application.parent_last_name,
        parent_phone=application.parent_phone,
        parent_email=application.parent_email,
        parent_occupation=application.parent_occupation,
        parent_address=application.parent_address,
        relationship_to_student=application.relationship_to_student,
        previous_school=application.previous_school,
        class_applying_for=application.class_applying_for,
        academic_session_id=application.academic_session_id,
        medical_conditions=application.medical_conditions,
        special_needs=application.special_needs,
        additional_info=application.additional_info,
        submission_date=datetime.utcnow(),
        school_id=school_id
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
    class_applying_for: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get all applications with filtering"""
    require_permission("admissions:view")(current_user)
    
    query = db.query(AdmissionApplication).filter(AdmissionApplication.school_id == school_id)
    
    if status:
        query = query.filter(AdmissionApplication.status == status)
    if class_applying_for:
        query = query.filter(AdmissionApplication.class_applying_for == class_applying_for)
    
    applications = query.order_by(AdmissionApplication.submission_date.desc()).offset(skip).limit(limit).all()
    return applications

@router.get("/admissions/applications/{application_id}", response_model=AdmissionApplicationSchema)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get details of a specific application"""
    application = db.query(AdmissionApplication).filter(
        AdmissionApplication.id == application_id,
        AdmissionApplication.school_id == school_id
    ).first()
    
    if not application:
        raise NotFoundException("Application not found")
    
    # Check permissions - applicants can view their own applications
    if not _can_access_application(current_user, application):
        require_permission("admissions:view")(current_user)
    
    return application

@router.put("/admissions/applications/{application_id}/status", response_model=AdmissionApplicationSchema)
async def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update application status"""
    require_permission("admissions:update_status")(current_user)
    
    application = db.query(AdmissionApplication).filter(
        AdmissionApplication.id == application_id,
        AdmissionApplication.school_id == school_id
    ).first()
    
    if not application:
        raise NotFoundException("Application not found")
    
    application.status = status_update.status
    application.review_date = datetime.utcnow()
    application.reviewed_by = current_user.id
    
    if status_update.rejection_reason:
        application.rejection_reason = status_update.rejection_reason
    
    if status_update.notes:
        application.notes = status_update.notes
    
    db.commit()
    db.refresh(application)
    
    return application

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
    
    # Check permissions
    if not _can_access_application(current_user, application):
        require_permission("admissions:upload_documents")(current_user)
    
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
        # Create user account for student
        from services.auth import get_password_hash
        import secrets
        
        # Generate username and temporary password
        username = f"{application.first_name.lower()}.{application.last_name.lower()}.{application.id}"
        temp_password = secrets.token_urlsafe(8)
        
        # Create user
        db_user = User(
            email=application.email or f"{username}@{school_id}.temp.edu",
            username=username,
            first_name=application.first_name,
            last_name=application.last_name,
            middle_name=application.middle_name,
            phone=application.phone,
            address=application.address,
            date_of_birth=application.date_of_birth,
            gender=application.gender,
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
            class_id=approval.class_id or application.class_applying_for,
            admission_date=approval.admission_date or date.today(),
            medical_info={"conditions": application.medical_conditions, "special_needs": application.special_needs},
            school_id=school_id
        )
        
        db.add(db_student)
        db.flush()
        
        # Create parent user if needed
        parent_username = f"parent.{application.parent_first_name.lower()}.{application.parent_last_name.lower()}.{db_student.id}"
        parent_temp_password = secrets.token_urlsafe(8)
        
        db_parent = User(
            email=application.parent_email,
            username=parent_username,
            first_name=application.parent_first_name,
            last_name=application.parent_last_name,
            phone=application.parent_phone,
            address=application.parent_address,
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
            relationship_type=application.relationship_to_student.lower(),
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

def _can_access_application(current_user: User, application: AdmissionApplication) -> bool:
    """Check if current user can access application"""
    # For now, we'll check if the user's email matches the parent email
    # In a more sophisticated system, you might have application codes or other methods
    return current_user.email == application.parent_email
