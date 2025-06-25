from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
from typing import Optional, List
from datetime import datetime, date


# --- Permission Schemas ---
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    module: str
    action: str
    resource: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class Permission(PermissionBase):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True


# --- Role Schemas ---
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Role(RoleBase):
    id: int
    school_id: Optional[int] = None
    is_system_role: bool = False
    is_active: bool = True
    permissions: List["Permission"] = []

    class Config:
        from_attributes = True


# --- Enums for User Schemas ---
class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None

    @field_validator('gender', mode='before')
    @classmethod
    def title_case_gender(cls, v: str) -> str:
        """Ensure gender is always in title case to match the Enum."""
        if isinstance(v, str):
            return v.title()
        return v


class UserCreate(UserBase):
    password: str
    school_id: Optional[int] = None
    role_ids: Optional[List[int]] = []


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None

    @field_validator('gender', mode='before')
    @classmethod
    def title_case_gender(cls, v: str) -> str:
        """Ensure gender is always in title case to match the Enum."""
        if isinstance(v, str):
            return v.title()
        return v


class User(UserBase):
    id: int
    school_id: int
    is_verified: bool = False
    is_approved: bool = False
    profile_picture_url: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    last_login: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    roles: List["Role"] = []

    class Config:
        from_attributes = True


class UserResponse(User):
    pass


# --- Other Schemas ---
class UserLogin(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class UserApproval(BaseModel):
    is_approved: bool
    rejection_reason: Optional[str] = None


# --- Rebuild Models ---
# This is crucial for resolving forward references.
# The order matters: dependencies must be rebuilt before dependents.
Permission.model_rebuild()
Role.model_rebuild()
User.model_rebuild()
UserResponse.model_rebuild()
Token.model_rebuild()
RoleUpdate.model_rebuild()

