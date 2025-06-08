from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import get_db
from models.teacher import Teacher, TeacherAssignment
from models.user import User
from models.academic import Subject, Class, AcademicSession
from schemas.teacher import (
    Teacher as TeacherSchema, TeacherCreate, TeacherUpdate,
    TeacherAssignment as TeacherAssignmentSchema, TeacherAssignmentCreate,
    TeacherStatusUpdate
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

@router.post("/teachers", response_model=TeacherSchema)
async def create_teacher(
    teacher: TeacherCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new teacher"""
    require_permission("teachers:create")(current_user)
    
    # Verify user exists and belongs to the school
    user = db.query(User).filter(
        User.id == teacher.user_id,
        User.school_id == school_id
    ).first()
    
    if not user:
        raise NotFoundException("User not found")
    
    # Check if teacher already exists for this user
    existing_teacher = db.query(Teacher).filter(Teacher.user_id == teacher.user_id).first()
    if existing_teacher:
        raise ValidationException("Teacher record already exists for this user")
    
    db_teacher = Teacher(
        user_id=teacher.user_id,
        employee_id=teacher.employee_id,
        department_id=teacher.department_id,
        hire_date=teacher.hire_date,
        teaching_qualification=teacher.teaching_qualification,
        specialization=teacher.specialization,
        years_experience=teacher.years_experience,
        salary_grade=teacher.salary_grade,
        contract_type=teacher.contract_type,
        emergency_contact_name=teacher.emergency_contact_name,
        emergency_contact_phone=teacher.emergency_contact_phone,
        school_id=school_id
    )
    
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    
    return db_teacher

@router.get("/teachers", response_model=List[TeacherSchema])
async def get_teachers(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get teachers"""
    require_permission("teachers:view")(current_user)
    
    query = db.query(Teacher).filter(Teacher.school_id == school_id)
    
    if department_id:
        query = query.filter(Teacher.department_id == department_id)
    
    if status:
        query = query.filter(Teacher.status == status)
    
    teachers = query.offset(skip).limit(limit).all()
    return teachers

@router.get("/teachers/{teacher_id}", response_model=TeacherSchema)
async def get_teacher(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific teacher"""
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id,
        Teacher.school_id == school_id
    ).first()
    
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    # Teachers can view their own profile, others need permission
    if current_user.id != teacher.user_id:
        require_permission("teachers:view")(current_user)
    
    return teacher

@router.put("/teachers/{teacher_id}", response_model=TeacherSchema)
async def update_teacher(
    teacher_id: int,
    teacher_update: TeacherUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a teacher"""
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id,
        Teacher.school_id == school_id
    ).first()
    
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    # Teachers can update their own profile, others need permission
    if current_user.id != teacher.user_id:
        require_permission("teachers:update")(current_user)
    
    # Update fields
    for field, value in teacher_update.dict(exclude_unset=True).items():
        setattr(teacher, field, value)
    
    db.commit()
    db.refresh(teacher)
    
    return teacher

@router.post("/teachers/assign", response_model=TeacherAssignmentSchema)
async def assign_teacher_to_subject_class(
    assignment: TeacherAssignmentCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Assign teacher to subject and class"""
    require_permission("teachers:assign")(current_user)
    
    # Verify teacher exists
    teacher = db.query(Teacher).filter(
        Teacher.id == assignment.teacher_id,
        Teacher.school_id == school_id
    ).first()
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    # Verify subject exists
    subject = db.query(Subject).filter(
        Subject.id == assignment.subject_id,
        Subject.school_id == school_id
    ).first()
    if not subject:
        raise NotFoundException("Subject not found")
    
    # Verify class exists
    class_obj = db.query(Class).filter(
        Class.id == assignment.class_id,
        Class.school_id == school_id
    ).first()
    if not class_obj:
        raise NotFoundException("Class not found")
    
    # Check if assignment already exists
    existing_assignment = db.query(TeacherAssignment).filter(
        TeacherAssignment.teacher_id == assignment.teacher_id,
        TeacherAssignment.subject_id == assignment.subject_id,
        TeacherAssignment.class_id == assignment.class_id,
        TeacherAssignment.academic_session_id == assignment.academic_session_id
    ).first()
    
    if existing_assignment:
        raise ValidationException("Teacher is already assigned to this subject and class")
    
    db_assignment = TeacherAssignment(
        teacher_id=assignment.teacher_id,
        subject_id=assignment.subject_id,
        class_id=assignment.class_id,
        academic_session_id=assignment.academic_session_id,
        is_class_teacher=assignment.is_class_teacher,
        assignment_date=assignment.assignment_date or date.today(),
        school_id=school_id
    )
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    return db_assignment

@router.delete("/teachers/assignments/{teacher_id}/{subject_id}/{class_id}")
async def remove_teacher_assignment(
    teacher_id: int,
    subject_id: int,
    class_id: int,
    academic_session_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Remove teacher assignment"""
    require_permission("teachers:unassign")(current_user)
    
    assignment = db.query(TeacherAssignment).filter(
        TeacherAssignment.teacher_id == teacher_id,
        TeacherAssignment.subject_id == subject_id,
        TeacherAssignment.class_id == class_id,
        TeacherAssignment.academic_session_id == academic_session_id,
        TeacherAssignment.school_id == school_id
    ).first()
    
    if not assignment:
        raise NotFoundException("Assignment not found")
    
    db.delete(assignment)
    db.commit()
    
    return {"message": "Assignment removed successfully"}

@router.get("/teachers/{teacher_id}/assignments", response_model=List[TeacherAssignmentSchema])
async def get_teacher_assignments(
    teacher_id: int,
    academic_session_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get teacher assignments"""
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id,
        Teacher.school_id == school_id
    ).first()
    
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    # Teachers can view their own assignments, others need permission
    if current_user.id != teacher.user_id:
        require_permission("teachers:view")(current_user)
    
    query = db.query(TeacherAssignment).filter(
        TeacherAssignment.teacher_id == teacher_id,
        TeacherAssignment.school_id == school_id
    )
    
    if academic_session_id:
        query = query.filter(TeacherAssignment.academic_session_id == academic_session_id)
    
    assignments = query.all()
    return assignments

@router.post("/teachers/{teacher_id}/unassign-all")
async def remove_all_teacher_assignments(
    teacher_id: int,
    academic_session_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Remove all teacher assignments"""
    require_permission("teachers:unassign_all")(current_user)
    
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id,
        Teacher.school_id == school_id
    ).first()
    
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    query = db.query(TeacherAssignment).filter(
        TeacherAssignment.teacher_id == teacher_id,
        TeacherAssignment.school_id == school_id
    )
    
    if academic_session_id:
        query = query.filter(TeacherAssignment.academic_session_id == academic_session_id)
    
    assignments = query.all()
    for assignment in assignments:
        db.delete(assignment)
    
    db.commit()
    
    return {"message": f"Removed {len(assignments)} assignments"}

@router.put("/teachers/{teacher_id}/status", response_model=TeacherSchema)
async def update_teacher_status(
    teacher_id: int,
    status_update: TeacherStatusUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update teacher status"""
    require_permission("teachers:update_status")(current_user)
    
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id,
        Teacher.school_id == school_id
    ).first()
    
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    teacher.status = status_update.status
    
    db.commit()
    db.refresh(teacher)
    
    return teacher
