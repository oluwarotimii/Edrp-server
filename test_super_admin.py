#!/usr/bin/env python3
"""
Test script to verify super admin creation functionality
"""
import os
import sys
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal, engine
from initialization import initialize_super_admin
from models.user import User, Role
from config import settings

def test_super_admin_creation():
    """Test the super admin creation functionality"""
    print("Testing super admin creation...")
    
    # Create a database session
    db: Session = SessionLocal()
    
    try:
        # Get initial count of users and roles
        initial_user_count = db.query(User).count()
        initial_super_admin_count = db.query(User).join(User.roles).filter(
            Role.name == "Super Admin"
        ).count()
        
        print(f"Initial user count: {initial_user_count}")
        print(f"Initial Super Admin count: {initial_super_admin_count}")
        
        # Initialize super admin
        created = initialize_super_admin(db)
        
        if created:
            print("✓ Super admin user was created successfully!")
        else:
            print("✓ Super admin user already existed, no new user was created.")
        
        # Get updated counts
        final_user_count = db.query(User).count()
        final_super_admin_count = db.query(User).join(User.roles).filter(
            Role.name == "Super Admin"
        ).count()
        
        print(f"Final user count: {final_user_count}")
        print(f"Final Super Admin count: {final_super_admin_count}")
        
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
        
        print("\n✓ Super admin creation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error during super admin creation test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_super_admin_creation()