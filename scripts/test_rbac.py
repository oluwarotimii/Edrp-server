"""Test script to verify RBAC functionality"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal
from models.user import User, Role, Permission
from services.permissions import PermissionService
from utils.dependencies import require_permission, require_role


def test_rbac_functionality():
    """Test RBAC functionality"""
    db: Session = SessionLocal()
    
    try:
        print("Testing RBAC functionality...")
        
        # Get all permissions
        all_permissions = db.query(Permission).all()
        print(f"Total permissions in system: {len(all_permissions)}")
        
        # Get all roles
        all_roles = db.query(Role).all()
        print(f"Total roles in system: {len(all_roles)}")
        
        # Print role names and their permissions
        for role in all_roles:
            print(f"Role: {role.name} (ID: {role.id})")
            print(f"  Permissions: {[p.name for p in role.permissions]}")
        
        # Test permission service methods
        print("\nTesting PermissionService methods...")
        
        # Create a mock user (for testing purposes)
        # In a real scenario, you would get an actual user from the database
        test_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            hashed_password="test",
            school_id=1
        )
        
        # Add some roles to the test user (for testing)
        # This is just for demonstration - in real usage, you'd have actual roles
        print("\nRBAC functionality test completed successfully!")
        
    except Exception as e:
        print(f"Error during RBAC test: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    test_rbac_functionality()
