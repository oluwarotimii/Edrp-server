from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random
import string
from datetime import datetime

from database import get_db
from models.school import School, SchoolSubscription
from models.user import User, Role, UserRole
from schemas.school import School as SchoolSchema, SchoolCreate, SchoolUpdate, JoinSchoolRequest
from utils.dependencies import get_current_user, require_permission
from utils.security import get_password_hash
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

def generate_join_code():
    """Generate a unique 8-character join code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.post("/schools", response_model=SchoolSchema)
async def register_school(
    school: SchoolCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new school and its first admin user.
    
    The school will be assigned a subdomain based on the school name if not provided.
    The subdomain must be unique across all schools.
    """
    # Check if school email already exists
    existing_school = db.query(School).filter(School.email == school.email).first()
    if existing_school:
        raise ValidationException("A school with this email already exists")

    # Check if admin email already exists
    existing_user = db.query(User).filter(User.email == school.admin_email).first()
    if existing_user:
        raise ValidationException("A user with this email already exists")
    
    # Get the Admin role
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    if not admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin role not found. Please seed the database with roles.",
        )

    # Use a transaction to ensure atomicity
    try:
        # Generate unique join code
        join_code = generate_join_code()
        while db.query(School).filter(School.join_code == join_code).first():
            join_code = generate_join_code()
            
        # Generate subdomain if not provided
        subdomain = getattr(school, 'subdomain', None)
        if not subdomain and hasattr(school, 'name'):
            from ..models.school import School as SchoolModel
            subdomain = SchoolModel.generate_subdomain(school.name)
            
            # Ensure the generated subdomain is unique
            counter = 1
            original_subdomain = subdomain
            while db.query(School).filter(School.subdomain == subdomain).first():
                subdomain = f"{original_subdomain}-{counter}"
                counter += 1
        
        # Validate subdomain if provided
        if subdomain:
            from ..schemas.school import SubdomainBase
            try:
                subdomain = SubdomainBase.validate_subdomain(subdomain)
                # Check if subdomain is already taken
                if db.query(School).filter(School.subdomain == subdomain).first():
                    raise ValidationException(f"Subdomain '{subdomain}' is already taken")
            except ValueError as e:
                raise ValidationException(str(e))
        else:
            raise ValidationException("Could not generate a valid subdomain from the school name")

        # Create the school
        # Create the school
        db_school = School(
            name=school.name,
            subdomain=subdomain,
            address=school.address,
            phone=school.phone,
            email=school.email,
            website=school.website,
            principal_name=school.principal_name,
            school_type=school.school_type.value,
            join_code=join_code,
            join_code_generated_at=datetime.utcnow(),
            is_approved=False  # Requires platform admin approval
        )
        db.add(db_school)
        db.flush()

        # Create Paystack subaccount for the school
        paystack_service = PaystackService()
        try:
            subaccount_response = await paystack_service.create_subaccount(
                business_name=school.name,
                settlement_bank=school.bank_name, # Assuming bank_name is part of SchoolCreate
                account_number=school.account_number # Assuming account_number is part of SchoolCreate
            )
            if subaccount_response and subaccount_response["status"]:
                db_school.paystack_subaccount_id = subaccount_response["data"]["subaccount_code"]
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create Paystack subaccount")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Paystack subaccount creation failed: {e}")

        # Create the admin user
        username = f"{school.admin_first_name.lower()}.{school.admin_last_name.lower()}"[:30]  # Generate username
        hashed_password = get_password_hash(school.admin_password)
        db_admin = User(
            username=username,
            first_name=school.admin_first_name,
            last_name=school.admin_last_name,
            email=school.admin_email,
            hashed_password=hashed_password,
            school_id=db_school.id,
            is_active=True,
            is_approved=True
        )
        db.add(db_admin)
        db.flush()

        # Assign the Admin role to the user
        user_role_association = UserRole(
            user_id=db_admin.id,
            role_id=admin_role.id,
            school_id=db_admin.school_id,
            assigned_by=None,  # No assigned_by for initial registration
            assigned_at=datetime.utcnow()
        )
        db.add(user_role_association)

        db.commit()
        db.refresh(db_school)
        
        return db_school
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        # Add more specific error handling
        if "UNIQUE constraint failed" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate entry found. Please check your inputs and try again."
            )
        elif "FOREIGN KEY constraint failed" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reference data. Please ensure all required data exists in the database."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during school registration: {error_msg}"
            )

@router.get("/schools", response_model=List[SchoolSchema])
async def get_schools(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all schools (admin only) or current user's school"""
    # Check if user has admin permissions to view all schools
    try:
        require_permission("schools:view_all")(current_user)
        schools = db.query(School).offset(skip).limit(limit).all()
    except:
        # Regular users can only see their own school
        schools = [db.query(School).filter(School.id == current_user.school_id).first()]
        
    return schools

@router.get("/schools/{school_id}", response_model=SchoolSchema)
async def get_school(
    school_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific school"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    # Check if user has permission to view this school
    if current_user.school_id != school_id:
        require_permission("schools:view_all")(current_user)
    
    return school

@router.put("/schools/{school_id}", response_model=SchoolSchema)
async def update_school(
    school_id: int,
    school_update: SchoolUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a school"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    # Check permissions
    if current_user.school_id != school_id:
        require_permission("schools:update_all")(current_user)
    else:
        require_permission("schools:update")(current_user)
    
    # Update fields
    for field, value in school_update.dict(exclude_unset=True).items():
        setattr(school, field, value)
    
    db.commit()
    db.refresh(school)
    
    return school

@router.post("/join-school")
async def join_school(
    join_request: JoinSchoolRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a school using join code"""
    school = db.query(School).filter(School.join_code == join_request.join_code).first()
    if not school:
        raise NotFoundException("Invalid join code")
    
    if not school.is_approved:
        raise ValidationException("School is not approved yet")

    # Check join code expiration
    if school.join_code_generated_at and (datetime.utcnow() - school.join_code_generated_at).total_seconds() > (48 * 3600):
        raise ValidationException("Join code has expired. Please request a new one from the school admin.")
    
    # Update user's school
    current_user.school_id = school.id
    current_user.is_approved = False  # Requires school admin approval
    
    db.commit()
    
    return {"message": f"Successfully joined {school.name}. Awaiting approval."}

@router.post("/schools/{school_id}/regenerate-code")
async def regenerate_join_code(
    school_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate school join code"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    # Check permissions
    if current_user.school_id != school_id:
        require_permission("schools:manage_all")(current_user)
    else:
        require_permission("schools:manage")(current_user)
    
    # Generate new join code
    new_code = generate_join_code()
    while db.query(School).filter(School.join_code == new_code).first():
        new_code = generate_join_code()
    
    school.join_code = new_code
    school.join_code_generated_at = datetime.utcnow()
    db.commit()
    
    return {"join_code": new_code}
