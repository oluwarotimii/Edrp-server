from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.user import User, Role, Permission, UserRole
from models.school import School
from schemas.user import Token, UserResponse, ChangePasswordRequest, UserRegisterAndJoin
from services.auth import create_access_token, verify_password, get_password_hash
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
    
    # Get user roles for token
    user_roles = [role.name for role in user.roles]
    
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "school_id": user.school_id,
            "roles": user_roles
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
    user_roles = [role.name for role in current_user.roles]
    
    access_token = create_access_token(
        data={
            "sub": current_user.username,
            "user_id": current_user.id,
            "school_id": current_user.school_id,
            "roles": user_roles
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