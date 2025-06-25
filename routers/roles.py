from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.user import User, Role, Permission
from schemas.user import Role as RoleSchema, RoleCreate, Permission as PermissionSchema, PermissionCreate, RoleUpdate
from utils.dependencies import require_role

router = APIRouter(
    prefix="/api/system",
    tags=["System Management"],
    dependencies=[Depends(require_role("super_admin"))] # Secure all endpoints
)

# --- Role Endpoints ---

@router.get("/roles", response_model=List[RoleSchema])
async def get_roles(db: Session = Depends(get_db)):
    """Get all roles"""
    return db.query(Role).all()

@router.post("/roles", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    """Create a new role"""
    new_role = Role(**role_data.model_dump())
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

@router.get("/roles/{role_id}", response_model=RoleSchema)
async def get_role(role_id: int, db: Session = Depends(get_db)):
    """Get a specific role by ID"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role

@router.put("/roles/{role_id}", response_model=RoleSchema)
async def update_role(role_id: int, role_data: RoleUpdate, db: Session = Depends(get_db)):
    """Update a role's details"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    
    update_data = role_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)
        
    db.commit()
    db.refresh(role)
    return role

# --- Permission Endpoints ---

@router.get("/permissions", response_model=List[PermissionSchema])
async def get_permissions(db: Session = Depends(get_db)):
    """Get all available permissions"""
    return db.query(Permission).all()

@router.post("/permissions", response_model=PermissionSchema, status_code=status.HTTP_201_CREATED)
async def create_permission(permission_data: PermissionCreate, db: Session = Depends(get_db)):
    """Create a new permission"""
    new_permission = Permission(**permission_data.model_dump())
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    return new_permission

# --- Role-Permission Mapping ---

@router.post("/roles/{role_id}/permissions/{permission_id}", response_model=RoleSchema)
async def assign_permission_to_role(role_id: int, permission_id: int, db: Session = Depends(get_db)):
    """Assign a permission to a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
        
    if permission in role.permissions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already assigned to this role")
        
    role.permissions.append(permission)
    db.commit()
    db.refresh(role)
    return role

@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=RoleSchema)
async def remove_permission_from_role(role_id: int, permission_id: int, db: Session = Depends(get_db)):
    """Remove a permission from a role"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
        
    if permission not in role.permissions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission not assigned to this role")
        
    role.permissions.remove(permission)
    db.commit()
    db.refresh(role)
    return role
