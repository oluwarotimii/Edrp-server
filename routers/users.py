from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.user import User, Role, Permission
from schemas.user import (
    User as UserSchema, UserCreate, UserUpdate, UserLogin, Token,
    Role as RoleSchema, RoleCreate, Permission as PermissionSchema,
    PermissionCreate, UserApproval
)
from services.auth import create_access_token, verify_password, get_password_hash
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException, UnauthorizedException

router = APIRouter()
role_router = APIRouter()
permission_router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login"""
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
    
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/users/pending", response_model=List[UserSchema])
async def get_pending_users(
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get users pending approval"""
    require_permission("users:approve")(current_user)
    
    users = db.query(User).filter(
        User.school_id == school_id,
        User.is_approved == False,
        User.is_active == True
    ).all()
    
    return users

@router.put("/users/{user_id}/approve", response_model=UserSchema)
async def approve_or_reject_user(
    user_id: int,
    approval: UserApproval,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Approve or reject a user"""
    require_permission("users:approve")(current_user)
    
    user = db.query(User).filter(
        User.id == user_id,
        User.school_id == school_id
    ).first()
    
    if not user:
        raise NotFoundException("User not found")
    
    user.is_approved = approval.is_approved
    
    # If rejected, deactivate the user
    if not approval.is_approved:
        user.is_active = False
    
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/users", response_model=List[UserSchema])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get users in the school"""
    require_permission("users:view")(current_user)
    
    query = db.query(User).filter(User.school_id == school_id)
    
    if role:
        query = query.join(User.roles).filter(Role.name == role)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific user"""
    user = db.query(User).filter(
        User.id == user_id,
        User.school_id == school_id
    ).first()
    
    if not user:
        raise NotFoundException("User not found")
    
    # Users can view their own profile, others need permission
    if current_user.id != user_id:
        require_permission("users:view")(current_user)
    
    return user

@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a user"""
    user = db.query(User).filter(
        User.id == user_id,
        User.school_id == school_id
    ).first()
    
    if not user:
        raise NotFoundException("User not found")
    
    # Users can update their own profile, others need permission
    if current_user.id != user_id:
        require_permission("users:update")(current_user)
    
    # Update fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Delete a user"""
    require_permission("users:delete")(current_user)
    
    user = db.query(User).filter(
        User.id == user_id,
        User.school_id == school_id
    ).first()
    
    if not user:
        raise NotFoundException("User not found")
    
    if user.id == current_user.id:
        raise ValidationException("Cannot delete your own account")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deleted successfully"}

# Role management routes
@role_router.get("/roles", response_model=List[RoleSchema])
async def get_roles(
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get all roles"""
    require_permission("roles:view")(current_user)
    
    roles = db.query(Role).filter(Role.school_id == school_id).all()
    return roles

@role_router.post("/roles", response_model=RoleSchema)
async def create_role(
    role: RoleCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new role"""
    require_permission("roles:create")(current_user)
    
    db_role = Role(
        name=role.name,
        description=role.description,
        school_id=school_id
    )
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    return db_role

@role_router.get("/roles/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific role"""
    require_permission("roles:view")(current_user)
    
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.school_id == school_id
    ).first()
    
    if not role:
        raise NotFoundException("Role not found")
    
    return role

@role_router.put("/roles/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: int,
    role_update: RoleCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a role"""
    require_permission("roles:update")(current_user)
    
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.school_id == school_id
    ).first()
    
    if not role:
        raise NotFoundException("Role not found")
    
    if role.is_system_role:
        raise ValidationException("Cannot update system role")
    
    role.name = role_update.name
    role.description = role_update.description
    
    db.commit()
    db.refresh(role)
    
    return role

# Permission management routes
@permission_router.get("/permissions", response_model=List[PermissionSchema])
async def get_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all permissions"""
    require_permission("permissions:view")(current_user)
    
    permissions = db.query(Permission).all()
    return permissions

@permission_router.post("/permissions", response_model=PermissionSchema)
async def create_permission(
    permission: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new permission"""
    require_permission("permissions:create")(current_user)
    
    db_permission = Permission(
        name=permission.name,
        description=permission.description,
        module=permission.module,
        action=permission.action,
        resource=permission.resource
    )
    
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    
    return db_permission

@permission_router.post("/roles/{role_id}/permissions/{permission_id}")
async def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Assign a permission to a role"""
    require_permission("roles:manage_permissions")(current_user)
    
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.school_id == school_id
    ).first()
    
    if not role:
        raise NotFoundException("Role not found")
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise NotFoundException("Permission not found")
    
    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()
    
    return {"message": "Permission assigned to role successfully"}

@permission_router.delete("/roles/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Remove a permission from a role"""
    require_permission("roles:manage_permissions")(current_user)
    
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.school_id == school_id
    ).first()
    
    if not role:
        raise NotFoundException("Role not found")
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise NotFoundException("Permission not found")
    
    if permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()
    
    return {"message": "Permission removed from role successfully"}
