from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.student import Student, StudentParent, StudentCustomField, StudentSubjectEnrollment
from models.user import User
from schemas.student import (
    Student as StudentSchema, StudentCreate, StudentUpdate,
    StudentParent as StudentParentSchema, StudentParentCreate,
    StudentCustomField as StudentCustomFieldSchema, StudentCustomFieldCreate,
    StudentSubjectEnrollment as StudentSubjectEnrollmentSchema, StudentSubjectEnrollmentCreate,
    StudentStatusUpdate, StudentGraduation, StudentWithdrawal
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

@router.post("/students", response_model=StudentSchema)
async def create_student(
    student: StudentCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new student"""
    require_permission("students:create")(current_user)
    
    # Verify user exists and belongs to the school
    user = db.query(User).filter(
        User.id == student.user_id,
        User.school_id == school_id
    ).first()
    
    if not user:
        raise NotFoundException("User not found")
    
    # Check if student already exists for this user
    existing_student = db.query(Student).filter(Student.user_id == student.user_id).first()
    if existing_student:
        raise ValidationException("Student record already exists for this user")
    
    db_student = Student(
        user_id=student.user_id,
        student_id=student.student_id,
        admission_number=student.admission_number,
        class_id=student.class_id,
        admission_date=student.admission_date,
        boarding_status=student.boarding_status,
        emergency_contact_name=student.emergency_contact_name,
        emergency_contact_phone=student.emergency_contact_phone,
        emergency_contact_relationship=student.emergency_contact_relationship,
        previous_school=student.previous_school,
        blood_group=student.blood_group,
        allergies=student.allergies,
        medications=student.medications,
        special_needs=student.special_needs,
        school_id=school_id
    )
    
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    return db_student

@router.get("/students", response_model=List[StudentSchema])
async def get_students(
    skip: int = 0,
    limit: int = 100,
    class_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get students"""
    require_permission("students:view")(current_user)
    
    query = db.query(Student).filter(Student.school_id == school_id)
    
    if class_id:
        query = query.filter(Student.class_id == class_id)
    
    if status:
        query = query.filter(Student.status == status)
    
    students = query.offset(skip).limit(limit).all()
    return students

@router.get("/students/{student_id}", response_model=StudentSchema)
async def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific student"""
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    # Check if user has permission or is the student/parent
    if not self._can_access_student(current_user, student, db):
        require_permission("students:view")(current_user)
    
    return student

@router.put("/students/{student_id}", response_model=StudentSchema)
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a student"""
    require_permission("students:update")(current_user)
    
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    # Update fields
    for field, value in student_update.dict(exclude_unset=True).items():
        setattr(student, field, value)
    
    db.commit()
    db.refresh(student)
    
    return student

@router.post("/students/{student_id}/parents/{parent_user_id}", response_model=StudentParentSchema)
async def link_parent_to_student(
    student_id: int,
    parent_user_id: int,
    parent_data: StudentParentCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Link a parent to a student"""
    require_permission("students:manage_parents")(current_user)
    
    # Verify student exists
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    if not student:
        raise NotFoundException("Student not found")
    
    # Verify parent user exists
    parent = db.query(User).filter(
        User.id == parent_user_id,
        User.school_id == school_id
    ).first()
    if not parent:
        raise NotFoundException("Parent user not found")
    
    # Check if link already exists
    existing_link = db.query(StudentParent).filter(
        StudentParent.student_id == student_id,
        StudentParent.parent_user_id == parent_user_id
    ).first()
    if existing_link:
        raise ValidationException("Parent is already linked to this student")
    
    db_parent_link = StudentParent(
        student_id=student_id,
        parent_user_id=parent_user_id,
        relationship_type=parent_data.relationship_type,
        is_primary_contact=parent_data.is_primary_contact,
        can_pick_up=parent_data.can_pick_up,
        school_id=school_id
    )
    
    db.add(db_parent_link)
    db.commit()
    db.refresh(db_parent_link)
    
    return db_parent_link

@router.delete("/students/{student_id}/parents/{parent_user_id}")
async def unlink_parent_from_student(
    student_id: int,
    parent_user_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Unlink a parent from a student"""
    require_permission("students:manage_parents")(current_user)
    
    parent_link = db.query(StudentParent).filter(
        StudentParent.student_id == student_id,
        StudentParent.parent_user_id == parent_user_id,
        StudentParent.school_id == school_id
    ).first()
    
    if not parent_link:
        raise NotFoundException("Parent link not found")
    
    db.delete(parent_link)
    db.commit()
    
    return {"message": "Parent unlinked successfully"}

@router.get("/students/{student_id}/parents", response_model=List[StudentParentSchema])
async def get_student_parents(
    student_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get student's parents"""
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    if not self._can_access_student(current_user, student, db):
        require_permission("students:view")(current_user)
    
    parents = db.query(StudentParent).filter(
        StudentParent.student_id == student_id,
        StudentParent.school_id == school_id
    ).all()
    
    return parents

@router.get("/parents/{parent_id}/children", response_model=List[StudentSchema])
async def get_parent_children(
    parent_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get parent's children"""
    # Check if current user is the parent or has permission
    if current_user.id != parent_id:
        require_permission("students:view")(current_user)
    
    student_links = db.query(StudentParent).filter(
        StudentParent.parent_user_id == parent_id,
        StudentParent.school_id == school_id
    ).all()
    
    student_ids = [link.student_id for link in student_links]
    students = db.query(Student).filter(Student.id.in_(student_ids)).all()
    
    return students

@router.post("/students/{student_id}/custom-fields", response_model=StudentCustomFieldSchema)
async def create_student_custom_field(
    student_id: int,
    field_data: StudentCustomFieldCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a custom field for a student"""
    require_permission("students:manage_custom_fields")(current_user)
    
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    if not student:
        raise NotFoundException("Student not found")
    
    db_field = StudentCustomField(
        student_id=student_id,
        field_name=field_data.field_name,
        field_value=field_data.field_value,
        field_type=field_data.field_type,
        school_id=school_id
    )
    
    db.add(db_field)
    db.commit()
    db.refresh(db_field)
    
    return db_field

@router.put("/students/{student_id}/status", response_model=StudentSchema)
async def update_student_status(
    student_id: int,
    status_update: StudentStatusUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update student status"""
    require_permission("students:update_status")(current_user)
    
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    student.status = status_update.status
    
    if status_update.status == "graduated" and status_update.effective_date:
        student.graduation_date = status_update.effective_date
    elif status_update.status == "withdrawn" and status_update.effective_date:
        student.withdrawal_date = status_update.effective_date
        if status_update.notes:
            student.withdrawal_reason = status_update.notes
    
    db.commit()
    db.refresh(student)
    
    return student

def _can_access_student(current_user: User, student: Student, db: Session) -> bool:
    """Check if current user can access student data"""
    # If user is the student themselves
    if current_user.id == student.user_id:
        return True
    
    # If user is a parent of the student
    parent_link = db.query(StudentParent).filter(
        StudentParent.student_id == student.id,
        StudentParent.parent_user_id == current_user.id
    ).first()
    
    return parent_link is not None
