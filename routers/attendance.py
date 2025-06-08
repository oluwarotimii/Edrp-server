from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from database import get_db
from models.attendance import AuthenticLocation, AttendanceRecord, TeacherAttendance
from models.student import Student
from models.teacher import Teacher
from models.user import User
from schemas.attendance import (
    AuthenticLocation as AuthenticLocationSchema, AuthenticLocationCreate, AuthenticLocationUpdate,
    AttendanceRecord as AttendanceRecordSchema, AttendanceRecordCreate, AttendanceRecordUpdate,
    BulkAttendanceCreate, LocationVerificationRequest,
    TeacherAttendance as TeacherAttendanceSchema, TeacherAttendanceCreate, TeacherAttendanceUpdate,
    AttendanceStatistics
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException
from utils.location import verify_location

router = APIRouter()

# Authentic Location endpoints
@router.post("/authentic-locations", response_model=AuthenticLocationSchema)
async def create_authentic_location(
    location: AuthenticLocationCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new authentic location"""
    require_permission("locations:create")(current_user)
    
    # If this is set as default, unset any existing default
    if location.is_default:
        db.query(AuthenticLocation).filter(
            AuthenticLocation.school_id == school_id,
            AuthenticLocation.is_default == True
        ).update({"is_default": False})
    
    db_location = AuthenticLocation(
        name=location.name,
        description=location.description,
        latitude=location.latitude,
        longitude=location.longitude,
        radius_meters=location.radius_meters,
        is_default=location.is_default,
        school_id=school_id
    )
    
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return db_location

@router.get("/authentic-locations", response_model=List[AuthenticLocationSchema])
async def get_authentic_locations(
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get authentic locations"""
    require_permission("locations:view")(current_user)
    
    locations = db.query(AuthenticLocation).filter(
        AuthenticLocation.school_id == school_id
    ).all()
    
    return locations

@router.get("/authentic-locations/{location_id}", response_model=AuthenticLocationSchema)
async def get_authentic_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific authentic location"""
    require_permission("locations:view")(current_user)
    
    location = db.query(AuthenticLocation).filter(
        AuthenticLocation.id == location_id,
        AuthenticLocation.school_id == school_id
    ).first()
    
    if not location:
        raise NotFoundException("Location not found")
    
    return location

@router.put("/authentic-locations/{location_id}", response_model=AuthenticLocationSchema)
async def update_authentic_location(
    location_id: int,
    location_update: AuthenticLocationUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update an authentic location"""
    require_permission("locations:update")(current_user)
    
    location = db.query(AuthenticLocation).filter(
        AuthenticLocation.id == location_id,
        AuthenticLocation.school_id == school_id
    ).first()
    
    if not location:
        raise NotFoundException("Location not found")
    
    # If setting as default, unset other defaults
    if location_update.is_default:
        db.query(AuthenticLocation).filter(
            AuthenticLocation.school_id == school_id,
            AuthenticLocation.id != location_id,
            AuthenticLocation.is_default == True
        ).update({"is_default": False})
    
    # Update fields
    for field, value in location_update.dict(exclude_unset=True).items():
        setattr(location, field, value)
    
    db.commit()
    db.refresh(location)
    
    return location

@router.post("/attendance/verify-location")
async def verify_attendance_location(
    verification: LocationVerificationRequest,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Verify if current location is valid for attendance"""
    # Get the location to verify against
    if verification.location_id:
        location = db.query(AuthenticLocation).filter(
            AuthenticLocation.id == verification.location_id,
            AuthenticLocation.school_id == school_id
        ).first()
    else:
        # Use default location
        location = db.query(AuthenticLocation).filter(
            AuthenticLocation.school_id == school_id,
            AuthenticLocation.is_default == True
        ).first()
    
    if not location:
        raise NotFoundException("No authentic location found")
    
    # Verify location
    is_valid = verify_location(
        verification.latitude,
        verification.longitude,
        location.latitude,
        location.longitude,
        location.radius_meters
    )
    
    return {
        "valid": is_valid,
        "location_name": location.name,
        "distance_meters": 0 if is_valid else None  # Calculate actual distance if needed
    }

# Student Attendance endpoints
@router.post("/attendance", response_model=AttendanceRecordSchema)
async def create_attendance_record(
    attendance: AttendanceRecordCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create an attendance record"""
    require_permission("attendance:take")(current_user)
    
    # Verify student exists
    student = db.query(Student).filter(
        Student.id == attendance.student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    # Check for existing record
    existing_record = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == attendance.student_id,
        AttendanceRecord.date == attendance.date,
        AttendanceRecord.session_name == attendance.session_name,
        AttendanceRecord.period_id == attendance.period_id
    ).first()
    
    if existing_record:
        raise ValidationException("Attendance already recorded for this session/period")
    
    # Verify location if coordinates provided
    location_verified = False
    if attendance.latitude and attendance.longitude:
        # Get default location for verification
        location = db.query(AuthenticLocation).filter(
            AuthenticLocation.school_id == school_id,
            AuthenticLocation.is_default == True
        ).first()
        
        if location:
            location_verified = verify_location(
                attendance.latitude,
                attendance.longitude,
                location.latitude,
                location.longitude,
                location.radius_meters
            )
    
    db_attendance = AttendanceRecord(
        student_id=attendance.student_id,
        date=attendance.date,
        session_name=attendance.session_name,
        status=attendance.status,
        period_id=attendance.period_id,
        subject_id=attendance.subject_id,
        notes=attendance.notes,
        marked_by=current_user.id,
        marked_at=datetime.utcnow(),
        location_verified=location_verified,
        latitude=attendance.latitude,
        longitude=attendance.longitude,
        school_id=school_id
    )
    
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    
    return db_attendance

@router.get("/attendance", response_model=List[AttendanceRecordSchema])
async def get_attendance_records(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = Query(None),
    date: Optional[date] = Query(None),
    class_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get attendance records"""
    require_permission("attendance:view")(current_user)
    
    query = db.query(AttendanceRecord).filter(AttendanceRecord.school_id == school_id)
    
    if student_id:
        query = query.filter(AttendanceRecord.student_id == student_id)
    
    if date:
        query = query.filter(AttendanceRecord.date == date)
    
    if class_id:
        query = query.join(Student).filter(Student.class_id == class_id)
    
    records = query.offset(skip).limit(limit).all()
    return records

@router.post("/attendance/bulk", response_model=List[AttendanceRecordSchema])
async def create_bulk_attendance(
    bulk_attendance: BulkAttendanceCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create bulk attendance records"""
    require_permission("attendance:take")(current_user)
    
    # Verify location if coordinates provided
    location_verified = False
    if bulk_attendance.latitude and bulk_attendance.longitude:
        location = db.query(AuthenticLocation).filter(
            AuthenticLocation.school_id == school_id,
            AuthenticLocation.is_default == True
        ).first()
        
        if location:
            location_verified = verify_location(
                bulk_attendance.latitude,
                bulk_attendance.longitude,
                location.latitude,
                location.longitude,
                location.radius_meters
            )
    
    created_records = []
    
    for record_data in bulk_attendance.attendance_records:
        # Check if record already exists
        existing = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == record_data["student_id"],
            AttendanceRecord.date == bulk_attendance.date,
            AttendanceRecord.session_name == bulk_attendance.session_name,
            AttendanceRecord.period_id == bulk_attendance.period_id
        ).first()
        
        if not existing:
            db_record = AttendanceRecord(
                student_id=record_data["student_id"],
                date=bulk_attendance.date,
                session_name=bulk_attendance.session_name,
                status=record_data["status"],
                period_id=bulk_attendance.period_id,
                subject_id=bulk_attendance.subject_id,
                notes=record_data.get("notes"),
                marked_by=current_user.id,
                marked_at=datetime.utcnow(),
                location_verified=location_verified,
                latitude=bulk_attendance.latitude,
                longitude=bulk_attendance.longitude,
                school_id=school_id
            )
            
            db.add(db_record)
            created_records.append(db_record)
    
    db.commit()
    
    for record in created_records:
        db.refresh(record)
    
    return created_records

@router.get("/attendance/{record_id}", response_model=AttendanceRecordSchema)
async def get_attendance_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific attendance record"""
    require_permission("attendance:view")(current_user)
    
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.id == record_id,
        AttendanceRecord.school_id == school_id
    ).first()
    
    if not record:
        raise NotFoundException("Attendance record not found")
    
    return record

@router.put("/attendance/{record_id}", response_model=AttendanceRecordSchema)
async def update_attendance_record(
    record_id: int,
    attendance_update: AttendanceRecordUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update an attendance record"""
    require_permission("attendance:update")(current_user)
    
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.id == record_id,
        AttendanceRecord.school_id == school_id
    ).first()
    
    if not record:
        raise NotFoundException("Attendance record not found")
    
    # Update fields
    for field, value in attendance_update.dict(exclude_unset=True).items():
        setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    
    return record

@router.get("/attendance/statistics/student/{student_id}", response_model=AttendanceStatistics)
async def get_student_attendance_statistics(
    student_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get student attendance statistics"""
    require_permission("attendance:view")(current_user)
    
    # Verify student exists
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    query = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student_id,
        AttendanceRecord.school_id == school_id
    )
    
    if start_date:
        query = query.filter(AttendanceRecord.date >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.date <= end_date)
    
    records = query.all()
    
    total_days = len(set(record.date for record in records))
    present_days = len([r for r in records if r.status == "present"])
    absent_days = len([r for r in records if r.status == "absent"])
    late_days = len([r for r in records if r.status == "late"])
    excused_days = len([r for r in records if r.status == "excused"])
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return AttendanceStatistics(
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        late_days=late_days,
        excused_days=excused_days,
        attendance_percentage=attendance_percentage,
        period="custom"
    )

# Teacher Attendance endpoints
@router.post("/teacher-attendance", response_model=TeacherAttendanceSchema)
async def create_teacher_attendance(
    attendance: TeacherAttendanceCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create teacher attendance record (clock in)"""
    # Teachers can clock in for themselves, admins can do it for others
    if current_user.id != attendance.teacher_id:
        require_permission("teacher_attendance:manage")(current_user)
    
    # Verify teacher exists
    teacher = db.query(Teacher).filter(
        Teacher.id == attendance.teacher_id,
        Teacher.school_id == school_id
    ).first()
    
    if not teacher:
        raise NotFoundException("Teacher not found")
    
    # Check for existing record today
    existing = db.query(TeacherAttendance).filter(
        TeacherAttendance.teacher_id == attendance.teacher_id,
        TeacherAttendance.date == attendance.date
    ).first()
    
    if existing:
        raise ValidationException("Attendance already recorded for today")
    
    # Verify location
    location_verified = False
    if attendance.clock_in_latitude and attendance.clock_in_longitude:
        location = db.query(AuthenticLocation).filter(
            AuthenticLocation.school_id == school_id,
            AuthenticLocation.is_default == True
        ).first()
        
        if location:
            location_verified = verify_location(
                attendance.clock_in_latitude,
                attendance.clock_in_longitude,
                location.latitude,
                location.longitude,
                location.radius_meters
            )
    
    db_attendance = TeacherAttendance(
        teacher_id=attendance.teacher_id,
        date=attendance.date,
        clock_in_time=datetime.utcnow(),
        status=attendance.status,
        notes=attendance.notes,
        location_verified=location_verified,
        clock_in_latitude=attendance.clock_in_latitude,
        clock_in_longitude=attendance.clock_in_longitude,
        school_id=school_id
    )
    
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    
    return db_attendance

@router.put("/teacher-attendance/{attendance_id}", response_model=TeacherAttendanceSchema)
async def update_teacher_attendance(
    attendance_id: int,
    attendance_update: TeacherAttendanceUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update teacher attendance (clock out)"""
    attendance = db.query(TeacherAttendance).filter(
        TeacherAttendance.id == attendance_id,
        TeacherAttendance.school_id == school_id
    ).first()
    
    if not attendance:
        raise NotFoundException("Attendance record not found")
    
    # Teachers can update their own, admins can update any
    teacher = db.query(Teacher).filter(Teacher.id == attendance.teacher_id).first()
    if current_user.id != teacher.user_id:
        require_permission("teacher_attendance:manage")(current_user)
    
    # Update fields
    for field, value in attendance_update.dict(exclude_unset=True).items():
        setattr(attendance, field, value)
    
    # Calculate total hours if clock out time is set
    if attendance.clock_in_time and attendance.clock_out_time:
        delta = attendance.clock_out_time - attendance.clock_in_time
        attendance.total_hours = delta.total_seconds() / 3600
    
    db.commit()
    db.refresh(attendance)
    
    return attendance
