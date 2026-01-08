#!/usr/bin/env python3
"""
Script to initialize default permissions and roles for the RBAC system.
This script ensures that all necessary permissions and default roles are created.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import Permission, Role
from services.permissions import PermissionService
from initialization import create_super_admin_role


def initialize_permissions_and_roles():
    """Initialize default permissions and system roles"""
    db: Session = SessionLocal()

    try:
        print("Initializing default permissions...")
        PermissionService.create_default_permissions(db)
        print("Default permissions created successfully!")

        print("Creating super admin role...")
        create_super_admin_role(db)
        print("Super admin role created successfully!")

        print("Initializing system default roles...")
        PermissionService.create_default_roles(db)
        print("System default roles created successfully!")

        print("RBAC initialization completed successfully!")
        print("\nNote: School-specific roles need to be created when each school is registered.")

    except Exception as e:
        print(f"Error during RBAC initialization: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    initialize_permissions_and_roles()
