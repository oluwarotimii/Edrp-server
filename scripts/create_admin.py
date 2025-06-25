"""Create a super admin user script"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db
from models.user import User, Role
from services.auth import get_password_hash

def create_super_admin(email: str, password: str):
    """Create a super admin user"""
    load_dotenv()
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL not found in .env file")
        return False
    
    try:
        # Add sslmode=require if not present
        if 'sslmode' not in DATABASE_URL:
            if '?' in DATABASE_URL:
                DATABASE_URL += "&sslmode=require"
            else:
                DATABASE_URL += "?sslmode=require"
        
        engine = create_engine(DATABASE_URL)
        
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Create a new session
        db = Session(engine)
        
        # Create roles if they don't exist
        roles = ["super_admin", "admin", "teacher", "student", "parent"]
        for role_name in roles:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name))
        db.commit()
        
        # Check if admin already exists
        if db.query(User).filter(User.email == email).first():
            print(f"ℹ️  User with email {email} already exists")
            return True
        
        # Create super admin user with all required fields
        username = email.split('@')[0]
        
        # First, check if we have a school
        from models.school import School
        school = db.query(School).first()
        
        if not school:
            # Create a default school if none exists
            school = School(
                name='System School',
                email='system@example.com',
                phone='+1234567890',
                address='System Address',
                city='System City',
                state='System State',
                country='System Country',
                postal_code='00000',
                is_active=True,
                is_approved=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(school)
            db.commit()
            db.refresh(school)
        
        # Now create the admin user
        admin = User(
            email=email,
            username=username,
            first_name='Admin',
            last_name='User',
            hashed_password=get_password_hash(password),
            is_active=True,
            is_verified=True,
            is_approved=True,
            # Required fields
            school_id=school.id,
            phone='+1234567890',
            address='System Generated',
            date_of_birth=datetime.utcnow().date(),
            gender='other',
            # Optional fields
            middle_name='',
            profile_picture_url='',
            emergency_contact='',
            emergency_phone='',
            last_login=datetime.utcnow(),
            failed_login_attempts=0,
            is_locked=False
        )
        
        # Add super_admin role
        super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
        if not super_admin_role:
            print("❌ Error: super_admin role not found")
            return False
            
        admin.roles.append(super_admin_role)
        db.add(admin)
        db.commit()
        
        print("✅ Super admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {str(e).split('\n')[0]}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e).split('\n')[0]}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create a super admin user')
    parser.add_argument('--email', default='admin@example.com', help='Admin email')
    parser.add_argument('--password', default='admin123', help='Admin password')
    
    args = parser.parse_args()
    
    print("🚀 Setting up super admin user...")
    if create_super_admin(args.email, args.password):
        sys.exit(0)
    else:
        sys.exit(1)
