from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.user import User, Role, Permission
from schemas.user import Token, UserResponse, ChangePasswordRequest
from services.auth import create_access_token, verify_password, get_password_hash
from utils.dependencies import get_current_user
from utils.exceptions import UnauthorizedException

router = APIRouter()

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
        "user_id": user.id,
        "username": user.username,
        "roles": user_roles,
        "school_id": user.school_id
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
        "user_id": current_user.id,
        "username": current_user.username,
        "roles": user_roles,
        "school_id": current_user.school_id
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