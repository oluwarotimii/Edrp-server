#!/usr/bin/env python3
"""
Script to reset and recreate the super admin user with valid email
"""
import os
import sys
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal, engine
from initialization import initialize_super_admin
from models.user import User, Role
from models.school import School

def reset_and_create_super_admin():
    """Reset and create the super admin user with valid email"""
    print("Resetting and creating super admin user...")
    
    # Create a database session
    db: Session = SessionLocal()
    
    try:
        # Delete existing super admin user and system school
        print("Removing existing super admin user and system school...")
        
        # Find and delete the super admin user
        super_admin_users = db.query(User).join(User.roles).filter(
            Role.name == "Super Admin"
        ).all()
        
        for user in super_admin_users:
            print(f"Deleting super admin user: {user.email}")
            db.delete(user)
        
        # Find and delete the system school
        system_schools = db.query(School).filter(
            School.subdomain == "systemadmin"
        ).all()
        
        for school in system_schools:
            print(f"Deleting system school: {school.name}")
            db.delete(school)
        
        db.commit()
        print("Existing super admin data removed.")
        
        # Now create the new super admin
        created = initialize_super_admin(db)
        
        if created:
            print("✓ New super admin user was created successfully!")
        else:
            print("✓ Super admin user already existed, no new user was created.")
        
        # Find the super admin user
        super_admin_user = db.query(User).join(User.roles).filter(
            Role.name == "Super Admin"
        ).first()
        
        if super_admin_user:
            print(f"✓ Found Super Admin user: {super_admin_user.email} ({super_admin_user.username})")
            print(f"  - Name: {super_admin_user.first_name} {super_admin_user.last_name}")
            print(f"  - Email: {super_admin_user.email}")
            print(f"  - Username: {super_admin_user.username}")
            print(f"  - Verified: {super_admin_user.is_verified}")
            print(f"  - Approved: {super_admin_user.is_approved}")
        else:
            print("✗ No Super Admin user found!")
            return False
        
        print("\n✓ Super admin reset and creation completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error during super admin reset: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    reset_and_create_super_admin()

