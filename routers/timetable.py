from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.timetable import Period, TimetableEntry
from models.academic import Class, Subject, AcademicSession
from models.teacher import Teacher
from models.user import User
from schemas.timetable import (
    Period as PeriodSchema, PeriodCreate, PeriodUpdate,
    TimetableEntry as TimetableEntrySchema, TimetableEntryCreate, TimetableEntryUpdate,
    ClassTimetable, TeacherTimetable
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

# Period endpoints
@router.post("/timetables/periods", response_model=PeriodSchema)
async def create_period(
    period: PeriodCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new period/time slot"""
    require_permission("periods:create")(current_user)
    
    # Check for overlapping periods
    overlapping = db.query(Period).filter(
        Period.school_id == school_id,
        Period.start_time < period.end_time,
        Period.end_time > period.start_time
    ).first()
    
    if overlapping:
        raise ValidationException("Period overlaps with existing period")
    
    db_period = Period(
        name=period.name,
        start_time=period.start_time,
        end_time=period.end_time,
        order_number=period.order_number,
        is_break=period.is_break,
        school_id=school_id
    )
    
    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    
    return db_period

@router.get("/timetables/periods", response_model=List[PeriodSchema])
async def get_periods(
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get all periods/time slots"""
    require_permission("periods:view")(current_user)
    
    periods = db.query(Period).filter(
        Period.school_id == school_id
    ).order_by(Period.order_number).all()
    
    return periods

@router.put("/timetables/periods/{period_id}", response_model=PeriodSchema)
async def update_period(
    period_id: int,
    period_update: PeriodUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a period/time slot"""
    require_permission("periods:update")(current_user)
    
    period = db.query(Period).filter(
        Period.id == period_id,
        Period.school_id == school_id
    ).first()
    
    if not period:
        raise NotFoundException("Period not found")
    
    # Check for overlaps if times are being updated
    if period_update.start_time or period_update.end_time:
        start_time = period_update.start_time or period.start_time
        end_time = period_update.end_time or period.end_time
        
        overlapping = db.query(Period).filter(
            Period.school_id == school_id,
            Period.id != period_id,
            Period.start_time < end_time,
            Period.end_time > start_time
        ).first()
        
        if overlapping:
            raise ValidationException("Updated period would overlap with existing period")
    
    # Update fields
    for field, value in period_update.dict(exclude_unset=True).items():
        setattr(period, field, value)
    
    db.commit()
    db.refresh(period)
    
    return period

@router.delete("/timetables/periods/{period_id}")
async def delete_period(
    period_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Delete a period/time slot"""
    require_permission("periods:delete")(current_user)
    
    period = db.query(Period).filter(
        Period.id == period_id,
        Period.school_id == school_id
    ).first()
    
    if not period:
        raise NotFoundException("Period not found")
    
    # Check if period is in use
    entries_count = db.query(TimetableEntry).filter(
        TimetableEntry.period_id == period_id
    ).count()
    
    if entries_count > 0:
        raise ValidationException("Cannot delete period with existing timetable entries")
    
    db.delete(period)
    db.commit()
    
    return {"message": "Period deleted successfully"}

# Timetable Entry endpoints
@router.post("/timetables", response_model=TimetableEntrySchema)
async def create_timetable_entry(
    entry: TimetableEntryCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new timetable entry"""
    require_permission("timetables:create")(current_user)
    
    # Verify all referenced entities exist
    class_obj = db.query(Class).filter(
        Class.id == entry.class_id,
        Class.school_id == school_id
    ).first()
    if not class_obj:
        raise NotFoundException("Class not found")
    
    subject = db.query(Subject).filter(
        Subject.id == entry.subject_id,
        Subject.school_id == school_id
    ).first()
    if not subject:
        raise NotFoundException("Subject not found")
    
    teacher = db.query(Teacher).filter(
        Teacher.id == entry.teacher_id,
        Teacher.school_id == school_id
    ).first()
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    period = db.query(Period).filter(
        Period.id == entry.period_id,
        Period.school_id == school_id
    ).first()
    if not period:
        raise NotFoundException("Period not found")
    
    session = db.query(AcademicSession).filter(
        AcademicSession.id == entry.academic_session_id,
        AcademicSession.school_id == school_id
    ).first()
    if not session:
        raise NotFoundException("Academic session not found")
    
    # Check for conflicts
    conflicts = db.query(TimetableEntry).filter(
        TimetableEntry.school_id == school_id,
        TimetableEntry.academic_session_id == entry.academic_session_id,
        TimetableEntry.day_of_week == entry.day_of_week,
        TimetableEntry.period_id == entry.period_id
    ).filter(
        (TimetableEntry.class_id == entry.class_id) |
        (TimetableEntry.teacher_id == entry.teacher_id)
    ).first()
    
    if conflicts:
        if conflicts.class_id == entry.class_id:
            raise ValidationException("Class already has a lesson scheduled for this time")
        if conflicts.teacher_id == entry.teacher_id:
            raise ValidationException("Teacher already has a lesson scheduled for this time")
    
    db_entry = TimetableEntry(
        class_id=entry.class_id,
        subject_id=entry.subject_id,
        teacher_id=entry.teacher_id,
        period_id=entry.period_id,
        day_of_week=entry.day_of_week,
        room_number=entry.room_number,
        academic_session_id=entry.academic_session_id,
        notes=entry.notes,
        school_id=school_id
    )
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    return db_entry

@router.get("/timetables", response_model=List[TimetableEntrySchema])
async def get_timetable_entries(
    skip: int = 0,
    limit: int = 100,
    class_id: Optional[int] = Query(None),
    teacher_id: Optional[int] = Query(None),
    day_of_week: Optional[int] = Query(None),
    academic_session_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get timetable entries"""
    require_permission("timetables:view")(current_user)
    
    query = db.query(TimetableEntry).filter(TimetableEntry.school_id == school_id)
    
    if class_id:
        query = query.filter(TimetableEntry.class_id == class_id)
    if teacher_id:
        query = query.filter(TimetableEntry.teacher_id == teacher_id)
    if day_of_week:
        query = query.filter(TimetableEntry.day_of_week == day_of_week)
    if academic_session_id:
        query = query.filter(TimetableEntry.academic_session_id == academic_session_id)
    
    entries = query.offset(skip).limit(limit).all()
    return entries

@router.get("/timetables/{entry_id}", response_model=TimetableEntrySchema)
async def get_timetable_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific timetable entry"""
    require_permission("timetables:view")(current_user)
    
    entry = db.query(TimetableEntry).filter(
        TimetableEntry.id == entry_id,
        TimetableEntry.school_id == school_id
    ).first()
    
    if not entry:
        raise NotFoundException("Timetable entry not found")
    
    return entry

@router.put("/timetables/{entry_id}", response_model=TimetableEntrySchema)
async def update_timetable_entry(
    entry_id: int,
    entry_update: TimetableEntryUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a timetable entry"""
    require_permission("timetables:update")(current_user)
    
    entry = db.query(TimetableEntry).filter(
        TimetableEntry.id == entry_id,
        TimetableEntry.school_id == school_id
    ).first()
    
    if not entry:
        raise NotFoundException("Timetable entry not found")
    
    # Check for conflicts if key fields are being updated
    if any([entry_update.class_id, entry_update.teacher_id, entry_update.period_id, entry_update.day_of_week]):
        class_id = entry_update.class_id or entry.class_id
        teacher_id = entry_update.teacher_id or entry.teacher_id
        period_id = entry_update.period_id or entry.period_id
        day_of_week = entry_update.day_of_week or entry.day_of_week
        
        conflicts = db.query(TimetableEntry).filter(
            TimetableEntry.school_id == school_id,
            TimetableEntry.id != entry_id,
            TimetableEntry.academic_session_id == entry.academic_session_id,
            TimetableEntry.day_of_week == day_of_week,
            TimetableEntry.period_id == period_id
        ).filter(
            (TimetableEntry.class_id == class_id) |
            (TimetableEntry.teacher_id == teacher_id)
        ).first()
        
        if conflicts:
            if conflicts.class_id == class_id:
                raise ValidationException("Class already has a lesson scheduled for this time")
            if conflicts.teacher_id == teacher_id:
                raise ValidationException("Teacher already has a lesson scheduled for this time")
    
    # Update fields
    for field, value in entry_update.dict(exclude_unset=True).items():
        setattr(entry, field, value)
    
    db.commit()
    db.refresh(entry)
    
    return entry

@router.delete("/timetables/{entry_id}")
async def delete_timetable_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Delete a timetable entry"""
    require_permission("timetables:delete")(current_user)
    
    entry = db.query(TimetableEntry).filter(
        TimetableEntry.id == entry_id,
        TimetableEntry.school_id == school_id
    ).first()
    
    if not entry:
        raise NotFoundException("Timetable entry not found")
    
    db.delete(entry)
    db.commit()
    
    return {"message": "Timetable entry deleted successfully"}

@router.get("/timetables/class/{class_id}", response_model=ClassTimetable)
async def get_class_timetable(
    class_id: int,
    academic_session_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get timetable for a specific class"""
    require_permission("timetables:view")(current_user)
    
    # Verify class exists
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise NotFoundException("Class not found")
    
    # Get current session if not specified
    if not academic_session_id:
        current_session = db.query(AcademicSession).filter(
            AcademicSession.school_id == school_id,
            AcademicSession.is_current == True
        ).first()
        if current_session:
            academic_session_id = current_session.id
        else:
            raise NotFoundException("No current academic session found")
    
    # Get all periods
    periods = db.query(Period).filter(
        Period.school_id == school_id
    ).order_by(Period.order_number).all()
    
    # Get timetable entries
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.class_id == class_id,
        TimetableEntry.academic_session_id == academic_session_id,
        TimetableEntry.school_id == school_id
    ).all()
    
    # Create 7x periods matrix
    timetable_matrix = [[None for _ in periods] for _ in range(7)]
    
    for entry in entries:
        day_index = entry.day_of_week - 1  # Convert to 0-based
        period_index = next((i for i, p in enumerate(periods) if p.id == entry.period_id), None)
        
        if period_index is not None and 0 <= day_index < 7:
            timetable_matrix[day_index][period_index] = {
                "entry_id": entry.id,
                "subject_name": entry.subject.name,
                "teacher_name": f"{entry.teacher.user.first_name} {entry.teacher.user.last_name}",
                "room_number": entry.room_number,
                "notes": entry.notes
            }
    
    return ClassTimetable(
        class_id=class_id,
        class_name=class_obj.name,
        academic_session_id=academic_session_id,
        timetable=timetable_matrix
    )

@router.get("/timetables/teacher/{teacher_id}", response_model=TeacherTimetable)
async def get_teacher_timetable(
    teacher_id: int,
    academic_session_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get timetable for a specific teacher"""
    # Verify teacher exists
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id,
        Teacher.school_id == school_id
    ).first()
    
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    # Teachers can view their own timetable, others need permission
    if current_user.id != teacher.user_id:
        require_permission("timetables:view")(current_user)
    
    # Get current session if not specified
    if not academic_session_id:
        current_session = db.query(AcademicSession).filter(
            AcademicSession.school_id == school_id,
            AcademicSession.is_current == True
        ).first()
        if current_session:
            academic_session_id = current_session.id
        else:
            raise NotFoundException("No current academic session found")
    
    # Get all periods
    periods = db.query(Period).filter(
        Period.school_id == school_id
    ).order_by(Period.order_number).all()
    
    # Get timetable entries
    entries = db.query(TimetableEntry).filter(
        TimetableEntry.teacher_id == teacher_id,
        TimetableEntry.academic_session_id == academic_session_id,
        TimetableEntry.school_id == school_id
    ).all()
    
    # Create 7x periods matrix
    timetable_matrix = [[None for _ in periods] for _ in range(7)]
    
    for entry in entries:
        day_index = entry.day_of_week - 1  # Convert to 0-based
        period_index = next((i for i, p in enumerate(periods) if p.id == entry.period_id), None)
        
        if period_index is not None and 0 <= day_index < 7:
            timetable_matrix[day_index][period_index] = {
                "entry_id": entry.id,
                "subject_name": entry.subject.name,
                "class_name": entry.class_assigned.name,
                "room_number": entry.room_number,
                "notes": entry.notes
            }
    
    return TeacherTimetable(
        teacher_id=teacher_id,
        teacher_name=f"{teacher.user.first_name} {teacher.user.last_name}",
        academic_session_id=academic_session_id,
        timetable=timetable_matrix
    )
