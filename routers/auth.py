from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import secrets
import string

from database import get_db
from models.user import User, Role, Permission, UserRole
from models.school import School
from schemas.user import Token, UserResponse, ChangePasswordRequest, UserRegisterAndJoin
from services.auth import create_access_token, verify_password, get_password_hash
from services.permissions import PermissionService
from utils.dependencies import get_current_user
from utils.exceptions import UnauthorizedException, ValidationException, NotFoundException

router = APIRouter()

@router.post("/register-and-join", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_and_join(
    user_data: UserRegisterAndJoin,
    db: Session = Depends(get_db)
):
    """Register a new user and join a school using a join code."""
    # Check if user with email or username already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    if existing_user:
        raise ValidationException("User with this email or username already exists.")

    # Find the school by join code
    school = db.query(School).filter(School.join_code == user_data.join_code).first()
    if not school:
        raise NotFoundException("Invalid join code.")
    
    # Check join code expiration
    if school.join_code_generated_at and (datetime.utcnow() - school.join_code_generated_at).total_seconds() > (48 * 3600):
        raise ValidationException("Join code has expired. Please request a new one from the school admin.")

    if not school.is_approved:
        raise ValidationException("School is not approved yet.")

    # Determine the role to assign
    role = db.query(Role).filter(Role.name == user_data.role_name, Role.school_id == school.id).first()
    if not role:
        # Fallback to 'student' role if the requested role doesn't exist for the school
        role = db.query(Role).filter(Role.name == "student", Role.school_id == school.id).first()
        if not role:
            raise HTTPException(status_code=500, detail="Default 'student' role not found for this school.")

    # Create the user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_name=user_data.middle_name,
        phone=user_data.phone,
        address=user_data.address,
        date_of_birth=user_data.date_of_birth,
        gender=user_data.gender,
        hashed_password=hashed_password,
        school_id=school.id,
        is_verified=False, # User needs to verify email
        is_approved=False  # Requires school admin approval
    )
    db.add(new_user)
    db.flush() # Flush to get user.id

    # Assign the role
    user_role_association = UserRole(
        user_id=new_user.id,
        role_id=role.id,
        school_id=school.id,
        assigned_by=None, # Self-registered
        assigned_at=datetime.utcnow()
    )
    db.add(user_role_association)

    db.commit()
    db.refresh(new_user)
    return new_user


from pydantic import BaseModel

class SchoolRegistrationRequest(BaseModel):
    school_name: str
    subdomain: str
    admin_email: str
    admin_username: str
    admin_password: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    principal_name: Optional[str] = None
    school_type: Optional[str] = "Primary"


@router.post("/register-school", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_school(
    request: SchoolRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new school and create the school admin user."""

    # Validate inputs
    if not request.school_name or not request.subdomain or not request.admin_email or not request.admin_username or not request.admin_password:
        raise ValidationException("Missing required fields: school_name, subdomain, admin_email, admin_username, admin_password")

    # Check if school with subdomain already exists
    existing_school = db.query(School).filter(School.subdomain == request.subdomain).first()
    if existing_school:
        raise ValidationException("School with this subdomain already exists.")

    # Check if user with email or username already exists
    existing_user = db.query(User).filter(
        (User.email == request.admin_email) | (User.username == request.admin_username)
    ).first()
    if existing_user:
        raise ValidationException("User with this email or username already exists.")

    # Generate a unique join code
    join_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    # Create the school
    new_school = School(
        name=request.school_name,
        subdomain=request.subdomain,
        address=request.address or "",
        phone=request.phone or "",
        email=request.email or request.admin_email,
        website=request.website or "",
        principal_name=request.principal_name or request.admin_username,
        join_code=join_code,
        school_type=request.school_type,
        is_approved=False,  # Requires approval
        is_active=True
    )
    db.add(new_school)
    db.flush()  # Flush to get school.id

    # Hash the password
    hashed_password = get_password_hash(request.admin_password)

    # Create the school admin user
    school_admin = User(
        email=request.admin_email,
        username=request.admin_username,
        first_name=request.principal_name.split()[0] if request.principal_name and ' ' in request.principal_name else request.admin_username,
        last_name=request.principal_name.split()[1] if request.principal_name and ' ' in request.principal_name and len(request.principal_name.split()) > 1 else "Admin",
        hashed_password=hashed_password,
        school_id=new_school.id,
        is_verified=True,  # Auto-verify for school admin
        is_approved=True,  # Auto-approve for school admin
        phone=request.phone
    )
    db.add(school_admin)
    db.flush()  # Flush to get user.id

    # Create default roles for the school
    PermissionService.create_school_default_roles(db, new_school.id)
    db.flush()  # Ensure roles are written to DB before assignment

    # Assign the school admin role to the user
    school_admin_role = db.query(Role).filter(
        Role.name == "school_admin",
        Role.school_id == new_school.id
    ).first()

    if school_admin_role:
        # Add the role to the user's roles relationship (using the association table)
        school_admin.roles.append(school_admin_role)

    db.commit()

    # Query the user again with joinedload to ensure roles are loaded
    from sqlalchemy.orm import joinedload
    school_admin = db.query(User).options(joinedload(User.roles)).filter(User.id == school_admin.id).first()

    # Generate access token for the new school admin
    user_roles = [role.name for role in school_admin.roles]

    access_token = create_access_token(
        data={
            "sub": school_admin.username,
            "user_id": school_admin.id,
            "school_id": school_admin.school_id,
            "roles": user_roles,
            "type": "user"  # Add the required type field
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": school_admin
    }

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedException("Incorrect username or password")
    
    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")
    
    if not user.is_approved:
        raise UnauthorizedException("Account is pending approval")
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    user.failed_login_attempts = 0
    db.commit()

    # Query the user again with joinedload to ensure roles are loaded
    from sqlalchemy.orm import joinedload
    user = db.query(User).options(joinedload(User.roles)).filter(User.id == user.id).first()

    # Get user roles for token
    user_roles = [role.name for role in user.roles]

    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "school_id": user.school_id,
            "roles": user_roles,
            "type": "user"  # Add the required type field
        }
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise UnauthorizedException("Current password is incorrect")
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """Refresh access token"""
    # Refresh the user to ensure roles are loaded
    db = get_db()
    try:
        from sqlalchemy.orm import joinedload
        fresh_user = db.query(User).options(joinedload(User.roles)).filter(User.id == current_user.id).first()
        user_roles = [role.name for role in fresh_user.roles]
    finally:
        db.close()

    access_token = create_access_token(
        data={
            "sub": current_user.username,
            "user_id": current_user.id,
            "school_id": current_user.school_id,
            "roles": user_roles,
            "type": "user"  # Add the required type field
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": current_user
    }

@router.get("/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_user)
):
    """Get current user permissions"""
    permissions = set()
    for role in current_user.roles:
        for permission in role.permissions:
            permissions.add(permission.name)
    
    return {"permissions": list(permissions)}