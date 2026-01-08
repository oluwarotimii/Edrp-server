#!/usr/bin/env python3
"""Script to initialize default roles for a specific school.
This script should be run when a new school is registered.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal
from services.permissions import PermissionService


def initialize_school_roles(school_id: int):
    """Initialize default roles for a specific school"""
    db: Session = SessionLocal()
    
    try:
        print(f"Initializing default roles for school ID: {school_id}")
        PermissionService.create_school_default_roles(db, school_id)
        print("School default roles created successfully!")
        
    except Exception as e:
        print(f"Error during school roles initialization: {str(e)}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python initialize_school_roles.py <school_id>")
        sys.exit(1)
    
    try:
        school_id = int(sys.argv[1])
        initialize_school_roles(school_id)
    except ValueError:
        print("Error: school_id must be an integer")
        sys.exit(1)
