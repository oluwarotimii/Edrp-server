from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random
import string

from database import get_db
from models.school import School, SchoolSubscription
from models.user import User
from schemas.school import School as SchoolSchema, SchoolCreate, SchoolUpdate, JoinSchoolRequest
from utils.dependencies import get_current_user, require_permission
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

def generate_join_code():
    """Generate a unique 8-character join code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.post("/schools", response_model=SchoolSchema)
async def register_school(
    school: SchoolCreate,
    db: Session = Depends(get_db)
):
    """Register a new school"""
    # Check if email already exists
    existing_school = db.query(School).filter(School.email == school.email).first()
    if existing_school:
        raise ValidationException("A school with this email already exists")
    
    # Generate unique join code
    join_code = generate_join_code()
    while db.query(School).filter(School.join_code == join_code).first():
        join_code = generate_join_code()
    
    db_school = School(
        name=school.name,
        address=school.address,
        phone=school.phone,
        email=school.email,
        website=school.website,
        principal_name=school.principal_name,
        is_boarding_school=school.is_boarding_school,
        school_type=school.school_type,
        join_code=join_code,
        is_approved=False  # Requires admin approval
    )
    
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    
    return db_school

@router.get("/schools", response_model=List[SchoolSchema])
async def get_schools(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all schools (admin only) or current user's school"""
    # Check if user has admin permissions to view all schools
    try:
        require_permission("schools:view_all")(current_user)
        schools = db.query(School).offset(skip).limit(limit).all()
    except:
        # Regular users can only see their own school
        schools = [db.query(School).filter(School.id == current_user.school_id).first()]
        
    return schools

@router.get("/schools/{school_id}", response_model=SchoolSchema)
async def get_school(
    school_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific school"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    # Check if user has permission to view this school
    if current_user.school_id != school_id:
        require_permission("schools:view_all")(current_user)
    
    return school

@router.put("/schools/{school_id}", response_model=SchoolSchema)
async def update_school(
    school_id: int,
    school_update: SchoolUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a school"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    # Check permissions
    if current_user.school_id != school_id:
        require_permission("schools:update_all")(current_user)
    else:
        require_permission("schools:update")(current_user)
    
    # Update fields
    for field, value in school_update.dict(exclude_unset=True).items():
        setattr(school, field, value)
    
    db.commit()
    db.refresh(school)
    
    return school

@router.post("/join-school")
async def join_school(
    join_request: JoinSchoolRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a school using join code"""
    school = db.query(School).filter(School.join_code == join_request.join_code).first()
    if not school:
        raise NotFoundException("Invalid join code")
    
    if not school.is_approved:
        raise ValidationException("School is not approved yet")
    
    # Update user's school
    current_user.school_id = school.id
    current_user.is_approved = False  # Requires school admin approval
    
    db.commit()
    
    return {"message": f"Successfully joined {school.name}. Awaiting approval."}

@router.post("/schools/{school_id}/regenerate-code")
async def regenerate_join_code(
    school_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate school join code"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    # Check permissions
    if current_user.school_id != school_id:
        require_permission("schools:manage_all")(current_user)
    else:
        require_permission("schools:manage")(current_user)
    
    # Generate new join code
    new_code = generate_join_code()
    while db.query(School).filter(School.join_code == new_code).first():
        new_code = generate_join_code()
    
    school.join_code = new_code
    db.commit()
    
    return {"join_code": new_code}
