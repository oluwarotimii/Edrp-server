from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from .base import BaseModel, TenantBaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .school import School
    from .communication import Message

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class User(TenantBaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    date_of_birth = Column(DateTime)
    gender = Column(String(10))
    profile_picture_url = Column(String(500))
    emergency_contact = Column(String(100))
    emergency_phone = Column(String(20))
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    # Relationships
    school: "School" = relationship("School", back_populates="users")
    roles: "List['Role']" = relationship("Role", secondary=user_roles, back_populates="users")
    sent_messages: "List['Message']" = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages: "List['Message']" = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")

class Role(TenantBaseModel):
    __tablename__ = "roles"
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_system_role = Column(Boolean, default=False)
    
    # Relationships
    users: "List['User']" = relationship("User", secondary=user_roles, back_populates="roles")
    permissions: "List['Permission']" = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(BaseModel):
    __tablename__ = "permissions"
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    module = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    resource = Column(String(50))
    
    # Relationships
    roles: "List['Role']" = relationship("Role", secondary=role_permissions, back_populates="permissions")

class UserRole(TenantBaseModel):
    __tablename__ = "user_roles_history"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime)
    removed_at = Column(DateTime)
    
class RolePermission(TenantBaseModel):
    __tablename__ = "role_permissions_history"
    
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime)
    removed_at = Column(DateTime)
