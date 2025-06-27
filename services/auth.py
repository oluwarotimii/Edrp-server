import os
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from config import settings
from models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username/email and password"""
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.is_locked = True
        
        db.commit()
        return None
    
    # Reset failed attempts on successful login
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        db.commit()
    
    return user

def check_account_status(user: User) -> None:
    """Check if user account is in good standing"""
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

class AuthService:
    """Service class for authentication operations"""
    
    @staticmethod
    def generate_temporary_password() -> str:
        """Generate a temporary password for new users"""
        import secrets
        import string
        
        # Generate 8-character password with letters and digits
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(8))
        return password
    
    @staticmethod
    def create_user_session(user: User, db: Session) -> dict:
        """Create user session and return token data"""
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "school_id": user.school_id
            }
        }
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit
    
    @staticmethod
    def reset_failed_attempts(user: User, db: Session) -> None:
        """Reset failed login attempts for user"""
        user.failed_login_attempts = 0
        user.is_locked = False
        db.commit()
    
    @staticmethod
    def unlock_account(user: User, db: Session) -> None:
        """Unlock user account"""
        user.is_locked = False
        user.failed_login_attempts = 0
        db.commit()
    
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str, db: Session) -> bool:
        """Change user password"""
        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            return False
        
        # Validate new password strength
        if not AuthService.validate_password_strength(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet security requirements"
            )
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True
    
    @staticmethod
    def generate_password_reset_token(user: User) -> str:
        """Generate password reset token"""
        data = {
            "sub": user.email,
            "type": "password_reset",
            "user_id": user.id
        }
        expires = timedelta(hours=24)  # Reset token expires in 24 hours
        return create_access_token(data, expires)
    
    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[dict]:
        """Verify password reset token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "password_reset":
                return None
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def reset_password(token: str, new_password: str, db: Session) -> bool:
        """Reset password using reset token"""
        payload = AuthService.verify_password_reset_token(token)
        if not payload:
            return False
        
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Validate new password strength
        if not AuthService.validate_password_strength(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet security requirements"
            )
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.failed_login_attempts = 0
        user.is_locked = False
        db.commit()
        return True
