"""
Module to handle initial data setup for the application.
This includes creating the super admin user and default roles/permissions.
"""
from sqlalchemy.orm import Session
from models.user import User, Role, Permission
from services.auth import get_password_hash
from config import settings
import logging

logger = logging.getLogger(__name__)

def create_super_admin_role(db: Session) -> Role:
    """Create or get the super admin role with system-wide permissions"""
    # Check if super admin role already exists (try both naming conventions)
    super_admin_role = db.query(Role).filter(
        (Role.name == "super_admin") | (Role.name == "Super Admin"),
        Role.is_system_role == True
    ).first()

    if super_admin_role:
        return super_admin_role

    # Create super admin role with the naming convention used in the database
    super_admin_role = Role(
        name="super_admin",  # Use consistent naming
        description="System-wide administrator with all permissions",
        is_system_role=True,
        school_id=None  # System-wide role, not tied to a specific school
    )
    db.add(super_admin_role)
    db.commit()
    db.refresh(super_admin_role)
    
    # Create system-wide permissions
    permissions = [
        {"name": "system:manage", "description": "Manage system-wide settings", "module": "system", "action": "manage", "resource": "system"},
        {"name": "schools:manage", "description": "Manage all schools", "module": "schools", "action": "manage", "resource": "schools"},
        {"name": "users:manage", "description": "Manage all users", "module": "users", "action": "manage", "resource": "users"},
        {"name": "roles:manage", "description": "Manage all roles and permissions", "module": "roles", "action": "manage", "resource": "roles"},
        {"name": "analytics:view", "description": "View system-wide analytics", "module": "analytics", "action": "view", "resource": "analytics"},
        {"name": "settings:manage", "description": "Manage system settings", "module": "settings", "action": "manage", "resource": "settings"},
        {"name": "dashboard:view", "description": "View super admin dashboard", "module": "dashboard", "action": "view", "resource": "dashboard"},
    ]
    
    # Create permissions if they don't exist
    for perm_data in permissions:
        existing_perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing_perm:
            permission = Permission(**perm_data)
            db.add(permission)
            db.flush()  # Get ID without committing
    
    # Get all system permissions and assign them to the super admin role
    all_system_permissions = db.query(Permission).filter(
        Permission.name.like("system:%") |
        Permission.name.like("schools:%") |
        Permission.name.like("users:%") |
        Permission.name.like("roles:%") |
        Permission.name.like("analytics:%") |
        Permission.name.like("settings:%") |
        Permission.name.like("dashboard:%")
    ).all()
    
    super_admin_role.permissions.extend(all_system_permissions)
    db.commit()
    
    logger.info("Super admin role and permissions created successfully")
    return super_admin_role

def create_system_school(db: Session) -> int:
    """Create a system school for the super admin user if it doesn't exist"""
    from models.school import School
    from datetime import datetime

    # Check if system school already exists
    system_school = db.query(School).filter(
        School.subdomain == "systemadmin"
    ).first()

    if system_school:
        return system_school.id

    # Create system school
    system_school = School(
        name="System Administration",
        subdomain="systemadmin",
        address="System Admin, Global",
        phone="+1234567890",
        email="system.admin@edrp.local",
        website="https://system.edrp.local",
        principal_name="System Admin",
        join_code="SYS001",
        school_type="System",
        is_approved=True,
        is_active=True
    )

    db.add(system_school)
    db.commit()
    db.refresh(system_school)

    logger.info(f"System school created with ID: {system_school.id}")
    return system_school.id

def create_super_admin_user(db: Session, email: str, username: str, password: str, first_name: str = "Super", last_name: str = "Admin") -> User:
    """Create or get the super admin user"""
    # Check if super admin user already exists
    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing_user:
        logger.info(f"Super admin user already exists with email: {email}")
        return existing_user

    # Ensure password is not longer than 72 characters for bcrypt
    if len(password) > 72:
        password = password[:72]

    # Create system school if it doesn't exist
    school_id = create_system_school(db)

    # Create super admin user
    hashed_password = get_password_hash(password)

    super_admin_user = User(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        phone="",
        address="",
        hashed_password=hashed_password,
        is_verified=True,
        is_approved=True,
        school_id=school_id  # Use the system school ID
    )

    db.add(super_admin_user)
    db.commit()
    db.refresh(super_admin_user)

    # Assign super admin role
    super_admin_role = create_super_admin_role(db)
    super_admin_user.roles.append(super_admin_role)
    db.commit()

    logger.info(f"Super admin user created successfully with email: {email}")
    return super_admin_user

def initialize_super_admin(db: Session) -> bool:
    """
    Initialize the super admin user if it doesn't exist.
    Returns True if super admin was created, False if it already existed.
    """
    # Get super admin credentials from environment variables or use defaults
    super_admin_email = settings.SUPER_ADMIN_EMAIL or "admin@edrp.local"
    super_admin_username = settings.SUPER_ADMIN_USERNAME or "superadmin"
    super_admin_password = settings.SUPER_ADMIN_PASSWORD or "SuperAdmin123!"
    # Ensure password is not longer than 72 characters for bcrypt
    if len(super_admin_password) > 72:
        super_admin_password = super_admin_password[:72]
    super_admin_first_name = settings.SUPER_ADMIN_FIRST_NAME or "Super"
    super_admin_last_name = settings.SUPER_ADMIN_LAST_NAME or "Admin"
    
    # Check if super admin user already exists
    existing_user = db.query(User).filter(
        (User.email == super_admin_email) | (User.username == super_admin_username)
    ).first()
    
    if existing_user:
        logger.info("Super admin user already exists, skipping initialization")
        return False
    
    # Create super admin user
    create_super_admin_user(
        db=db,
        email=super_admin_email,
        username=super_admin_username,
        password=super_admin_password,
        first_name=super_admin_first_name,
        last_name=super_admin_last_name
    )
    
    logger.info("Super admin initialization completed successfully")
    return True

# Add default values to settings for super admin credentials
def add_super_admin_settings():
    """Add super admin settings to the Settings class"""
    # This function is just for documentation purposes
    # The actual settings are added in config.py
    pass