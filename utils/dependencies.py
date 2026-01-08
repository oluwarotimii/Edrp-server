from typing import Generator, Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database import get_db
from models.user import User, ProspectiveApplicant
from models.school import School
from services.auth import verify_token
from config import settings

# Security scheme for JWT authentication
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Union[User, ProspectiveApplicant]:
    """Get current authenticated user (either User or ProspectiveApplicant)"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    if token_type == "user":
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked due to multiple failed login attempts"
            )
        
        if not user.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is pending approval"
            )
        return user
    elif token_type == "prospective_applicant":
        applicant = db.query(ProspectiveApplicant).filter(
            ProspectiveApplicant.email == username
        ).first()
        
        if applicant is None:
            raise credentials_exception
        
        if not applicant.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not verified. Please check your email for verification link."
            )
        return applicant
    else:
        raise credentials_exception

async def get_current_school(
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> int:
    """Get current user's school ID"""
    
    if not current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any school"
        )
    
    school = db.query(School).filter(
        School.id == current_user.school_id,
        School.is_active == True
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found or inactive"
        )
    
    return current_user.school_id

def require_permission(permission_name: str):
    """Dependency factory to require specific permission"""

    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if current user has required permission"""

        if not isinstance(current_user, User):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authenticated users can perform this action."
            )

        # Use the PermissionService to check permissions
        from services.permissions import PermissionService
        has_perm = PermissionService.has_permission(current_user, permission_name, db)

        # Check if user has the required permission
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission_name}"
            )

        return current_user

    return permission_checker

def require_any_permission(permission_names: list):
    """Dependency factory to require any of the specified permissions"""

    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if current user has any of the required permissions"""

        if not isinstance(current_user, User):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authenticated users can perform this action."
            )

        # Use the PermissionService to check permissions
        from services.permissions import PermissionService
        has_any = PermissionService.has_any_permission(current_user, permission_names, db)

        # Check if user has any of the required permissions
        if not has_any:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required any of: {', '.join(permission_names)}"
            )

        return current_user

    return permission_checker

def require_all_permissions(permission_names: list):
    """Dependency factory to require all of the specified permissions"""

    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if current user has all of the required permissions"""

        if not isinstance(current_user, User):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authenticated users can perform this action."
            )

        # Use the PermissionService to check permissions
        from services.permissions import PermissionService
        has_all = PermissionService.has_all_permissions(current_user, permission_names, db)

        # Check if user has all of the required permissions
        if not has_all:
            # Find which permissions are missing
            user_permissions = set()
            for role in current_user.roles:
                for permission in role.permissions:
                    user_permissions.add(permission.name)

            missing_permissions = [perm for perm in permission_names if perm not in user_permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing: {', '.join(missing_permissions)}"
            )

        return current_user

    return permission_checker

def require_role(role_name: str):
    """Dependency factory to require specific role"""

    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if current user has required role"""

        if not isinstance(current_user, User):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authenticated users can perform this action."
            )

        user_roles = [role.name for role in current_user.roles]

        # Handle both naming conventions for super_admin role
        if role_name == "super_admin" and "super_admin" in user_roles:
            return current_user
        elif role_name == "super_admin" and "Super Admin" in user_roles:
            # Also accept "Super Admin" as equivalent to "super_admin"
            return current_user

        if role_name not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {role_name}"
            )

        return current_user

    return role_checker

def require_any_role(role_names: list):
    """Dependency factory to require any of the specified roles"""

    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        """Check if current user has any of the required roles"""

        if not isinstance(current_user, User):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authenticated users can perform this action."
            )

        user_roles = [role.name for role in current_user.roles]

        # Check if any of the required roles match (with fallback for naming inconsistencies)
        has_required_role = False
        for required_role in role_names:
            if required_role in user_roles:
                has_required_role = True
                break
            # Handle super_admin naming inconsistency
            elif required_role == "super_admin" and "Super Admin" in user_roles:
                has_required_role = True
                break
            elif required_role == "Super Admin" and "super_admin" in user_roles:
                has_required_role = True
                break

        if not has_required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required any role: {', '.join(role_names)}"
            )

        return current_user

    return role_checker

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Union[User, ProspectiveApplicant]]:
    """Get current user if authenticated, otherwise return None"""
    
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type is None:
            return None
    except JWTError:
        return None
    
    if token_type == "user":
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.is_active and not user.is_locked and user.is_approved:
            return user
    elif token_type == "prospective_applicant":
        applicant = db.query(ProspectiveApplicant).filter(
            ProspectiveApplicant.email == username
        ).first()
        
        if applicant and applicant.is_verified:
            return applicant
    
    return None

async def get_user_school(
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> School:
    """Get current user's school object"""
    
    if not current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any school"
        )
    
    school = db.query(School).filter(
        School.id == current_user.school_id,
        School.is_active == True
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found or inactive"
        )
    
    return school

def require_school_approved():
    """Dependency to require school to be approved"""
    
    def school_checker(
        school: School = Depends(get_user_school)
    ) -> School:
        """Check if school is approved"""
        
        if not school.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="School is not approved for this operation"
            )
        
        return school
    
    return school_checker

async def validate_school_access(
    school_id: int,
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user)
) -> bool:
    """Validate that current user has access to the specified school"""
    
    # Super admins can access any school
    if isinstance(current_user, User):
        user_roles = [role.name for role in current_user.roles]
        if "super_admin" in user_roles:
            return True
    
    # Other users can only access their own school
    if current_user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this school"
        )
    
    return True

def require_same_school_or_admin(resource_school_id: int):
    """Dependency factory to require same school or admin access"""
    
    def school_checker(
        current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user)
    ) -> Union[User, ProspectiveApplicant]:
        """Check if user can access resource from specified school"""
        
        if isinstance(current_user, User):
            user_roles = [role.name for role in current_user.roles]
            # Super admins can access any school
            if "super_admin" in user_roles:
                return current_user
        
        # Other users must be from the same school
        if current_user.school_id != resource_school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this school's resources"
            )
        
        return current_user
    
    return school_checker

# Rate limiting dependency (placeholder for implementation with Redis)
async def rate_limit(
    identifier: str,
    max_requests: int = 100,
    window_seconds: int = 3600,
    current_user: Union[User, ProspectiveApplicant] = Depends(get_current_user)
) -> bool:
    """Rate limiting dependency"""
    
    # In a real implementation, this would use Redis to track request counts
    # For now, just return True
    return True

# IP address whitelist dependency
async def require_whitelisted_ip(
    request,
    allowed_ips: Optional[list] = None
) -> bool:
    """Require request to come from whitelisted IP"""
    
    if not allowed_ips:
        return True
    
    from utils.security import SecurityUtils
    client_ip = SecurityUtils.get_client_ip(request)
    
    if client_ip not in allowed_ips:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address"
        )
    
    return True

# API key authentication (for external integrations)
async def require_api_key(
    api_key: str,
    db: Session = Depends(get_db)
) -> bool:
    """Require valid API key for access"""
    
    # In a real implementation, you would:
    # 1. Check api_key against a table of valid API keys
    # 2. Verify the key is active and not expired
    # 3. Log the API usage
    
    # For now, just check against a setting
    valid_api_keys = getattr(settings, 'VALID_API_KEYS', [])
    
    if api_key not in valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True
