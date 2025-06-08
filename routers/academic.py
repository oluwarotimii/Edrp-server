from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.academic import Department, Class, Subject, AcademicSession, Term
from models.user import User
from schemas.academic import (
    Department as DepartmentSchema, DepartmentCreate, DepartmentUpdate,
    Class as ClassSchema, ClassCreate, ClassUpdate,
    Subject as SubjectSchema, SubjectCreate, SubjectUpdate,
    AcademicSession as AcademicSessionSchema, AcademicSessionCreate, AcademicSessionUpdate,
    Term as TermSchema, TermCreate, TermUpdate
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

# Department endpoints
@router.post("/departments", response_model=DepartmentSchema)
async def create_department(
    department: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new department"""
    require_permission("departments:create")(current_user)
    
    db_department = Department(
        name=department.name,
        description=department.description,
        head_teacher_id=department.head_teacher_id,
        school_id=school_id
    )
    
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    
    return db_department

@router.get("/departments", response_model=List[DepartmentSchema])
async def get_departments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get departments"""
    require_permission("departments:view")(current_user)
    
    departments = db.query(Department).filter(
        Department.school_id == school_id
    ).offset(skip).limit(limit).all()
    
    return departments

@router.get("/departments/{department_id}", response_model=DepartmentSchema)
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific department"""
    require_permission("departments:view")(current_user)
    
    department = db.query(Department).filter(
        Department.id == department_id,
        Department.school_id == school_id
    ).first()
    
    if not department:
        raise NotFoundException("Department not found")
    
    return department

@router.put("/departments/{department_id}", response_model=DepartmentSchema)
async def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a department"""
    require_permission("departments:update")(current_user)
    
    department = db.query(Department).filter(
        Department.id == department_id,
        Department.school_id == school_id
    ).first()
    
    if not department:
        raise NotFoundException("Department not found")
    
    # Update fields
    for field, value in department_update.dict(exclude_unset=True).items():
        setattr(department, field, value)
    
    db.commit()
    db.refresh(department)
    
    return department

# Class endpoints
@router.post("/classes", response_model=ClassSchema)
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new class"""
    require_permission("classes:create")(current_user)
    
    db_class = Class(
        name=class_data.name,
        description=class_data.description,
        class_teacher_id=class_data.class_teacher_id,
        capacity=class_data.capacity,
        room_number=class_data.room_number,
        grade_level=class_data.grade_level,
        school_id=school_id
    )
    
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    
    return db_class

@router.get("/classes", response_model=List[ClassSchema])
async def get_classes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get classes"""
    require_permission("classes:view")(current_user)
    
    classes = db.query(Class).filter(
        Class.school_id == school_id
    ).offset(skip).limit(limit).all()
    
    return classes

@router.get("/classes/{class_id}", response_model=ClassSchema)
async def get_class(
    class_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific class"""
    require_permission("classes:view")(current_user)
    
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise NotFoundException("Class not found")
    
    return class_obj

@router.put("/classes/{class_id}", response_model=ClassSchema)
async def update_class(
    class_id: int,
    class_update: ClassUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a class"""
    require_permission("classes:update")(current_user)
    
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise NotFoundException("Class not found")
    
    # Update fields
    for field, value in class_update.dict(exclude_unset=True).items():
        setattr(class_obj, field, value)
    
    db.commit()
    db.refresh(class_obj)
    
    return class_obj

# Subject endpoints
@router.post("/subjects", response_model=SubjectSchema)
async def create_subject(
    subject: SubjectCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new subject"""
    require_permission("subjects:create")(current_user)
    
    db_subject = Subject(
        name=subject.name,
        code=subject.code,
        description=subject.description,
        department_id=subject.department_id,
        is_core=subject.is_core,
        credit_units=subject.credit_units,
        school_id=school_id
    )
    
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    
    return db_subject

@router.get("/subjects", response_model=List[SubjectSchema])
async def get_subjects(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get subjects"""
    require_permission("subjects:view")(current_user)
    
    query = db.query(Subject).filter(Subject.school_id == school_id)
    
    if department_id:
        query = query.filter(Subject.department_id == department_id)
    
    subjects = query.offset(skip).limit(limit).all()
    
    return subjects

@router.get("/subjects/{subject_id}", response_model=SubjectSchema)
async def get_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific subject"""
    require_permission("subjects:view")(current_user)
    
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.school_id == school_id
    ).first()
    
    if not subject:
        raise NotFoundException("Subject not found")
    
    return subject

@router.put("/subjects/{subject_id}", response_model=SubjectSchema)
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a subject"""
    require_permission("subjects:update")(current_user)
    
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.school_id == school_id
    ).first()
    
    if not subject:
        raise NotFoundException("Subject not found")
    
    # Update fields
    for field, value in subject_update.dict(exclude_unset=True).items():
        setattr(subject, field, value)
    
    db.commit()
    db.refresh(subject)
    
    return subject

# Academic Session endpoints
@router.post("/academic-sessions", response_model=AcademicSessionSchema)
async def create_academic_session(
    session: AcademicSessionCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new academic session"""
    require_permission("academic_sessions:create")(current_user)
    
    # If this is marked as current, unset any existing current session
    if session.is_current:
        db.query(AcademicSession).filter(
            AcademicSession.school_id == school_id,
            AcademicSession.is_current == True
        ).update({"is_current": False})
    
    db_session = AcademicSession(
        name=session.name,
        start_date=session.start_date,
        end_date=session.end_date,
        is_current=session.is_current,
        school_id=school_id
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

@router.get("/academic-sessions", response_model=List[AcademicSessionSchema])
async def get_academic_sessions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get academic sessions"""
    require_permission("academic_sessions:view")(current_user)
    
    sessions = db.query(AcademicSession).filter(
        AcademicSession.school_id == school_id
    ).offset(skip).limit(limit).all()
    
    return sessions

@router.get("/academic-sessions/{session_id}", response_model=AcademicSessionSchema)
async def get_academic_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific academic session"""
    require_permission("academic_sessions:view")(current_user)
    
    session = db.query(AcademicSession).filter(
        AcademicSession.id == session_id,
        AcademicSession.school_id == school_id
    ).first()
    
    if not session:
        raise NotFoundException("Academic session not found")
    
    return session

@router.put("/academic-sessions/{session_id}", response_model=AcademicSessionSchema)
async def update_academic_session(
    session_id: int,
    session_update: AcademicSessionUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update an academic session"""
    require_permission("academic_sessions:update")(current_user)
    
    session = db.query(AcademicSession).filter(
        AcademicSession.id == session_id,
        AcademicSession.school_id == school_id
    ).first()
    
    if not session:
        raise NotFoundException("Academic session not found")
    
    # If setting as current, unset other current sessions
    if session_update.is_current:
        db.query(AcademicSession).filter(
            AcademicSession.school_id == school_id,
            AcademicSession.id != session_id,
            AcademicSession.is_current == True
        ).update({"is_current": False})
    
    # Update fields
    for field, value in session_update.dict(exclude_unset=True).items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    
    return session

# Term endpoints
@router.post("/terms", response_model=TermSchema)
async def create_term(
    term: TermCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new term"""
    require_permission("terms:create")(current_user)
    
    # Verify academic session exists
    session = db.query(AcademicSession).filter(
        AcademicSession.id == term.academic_session_id,
        AcademicSession.school_id == school_id
    ).first()
    
    if not session:
        raise NotFoundException("Academic session not found")
    
    # If this is marked as current, unset any existing current term
    if term.is_current:
        db.query(Term).filter(
            Term.school_id == school_id,
            Term.is_current == True
        ).update({"is_current": False})
    
    db_term = Term(
        name=term.name,
        academic_session_id=term.academic_session_id,
        start_date=term.start_date,
        end_date=term.end_date,
        is_current=term.is_current,
        school_id=school_id
    )
    
    db.add(db_term)
    db.commit()
    db.refresh(db_term)
    
    return db_term

@router.get("/terms", response_model=List[TermSchema])
async def get_terms(
    skip: int = 0,
    limit: int = 100,
    academic_session_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get terms"""
    require_permission("terms:view")(current_user)
    
    query = db.query(Term).filter(Term.school_id == school_id)
    
    if academic_session_id:
        query = query.filter(Term.academic_session_id == academic_session_id)
    
    terms = query.offset(skip).limit(limit).all()
    
    return terms

@router.get("/terms/{term_id}", response_model=TermSchema)
async def get_term(
    term_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific term"""
    require_permission("terms:view")(current_user)
    
    term = db.query(Term).filter(
        Term.id == term_id,
        Term.school_id == school_id
    ).first()
    
    if not term:
        raise NotFoundException("Term not found")
    
    return term

@router.put("/terms/{term_id}", response_model=TermSchema)
async def update_term(
    term_id: int,
    term_update: TermUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a term"""
    require_permission("terms:update")(current_user)
    
    term = db.query(Term).filter(
        Term.id == term_id,
        Term.school_id == school_id
    ).first()
    
    if not term:
        raise NotFoundException("Term not found")
    
    # If setting as current, unset other current terms
    if term_update.is_current:
        db.query(Term).filter(
            Term.school_id == school_id,
            Term.id != term_id,
            Term.is_current == True
        ).update({"is_current": False})
    
    # Update fields
    for field, value in term_update.dict(exclude_unset=True).items():
        setattr(term, field, value)
    
    db.commit()
    db.refresh(term)
    
    return term
