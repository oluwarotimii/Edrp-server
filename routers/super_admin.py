from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models.school import School
from models.user import User, Role, Permission
from models.student import Student
from models.teacher import Teacher
from models.fee import Payment
from models.attendance import AttendanceRecord
from schemas.user import UserCreate, UserResponse
from schemas.school import SchoolResponse, SchoolUpdate
from utils.dependencies import get_current_user, require_role
from utils.exceptions import NotFoundException, ForbiddenException

router = APIRouter()

# Super Admin Dashboard
@router.get("/dashboard")
async def get_super_admin_dashboard(
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Get super admin dashboard statistics"""
    
    # System-wide statistics
    total_schools = db.query(School).count()
    active_schools = db.query(School).filter(School.is_active == True).count()
    pending_schools = db.query(School).filter(School.is_approved == False).count()
    
    total_users = db.query(User).count()
    total_students = db.query(Student).count()
    total_teachers = db.query(Teacher).count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_schools_30d = db.query(School).filter(School.created_at >= thirty_days_ago).count()
    new_users_30d = db.query(User).filter(User.created_at >= thirty_days_ago).count()
    
    # Revenue statistics
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == 'completed'
    ).scalar() or 0
    
    monthly_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == 'completed',
        Payment.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Top performing schools by student count
    top_schools = db.query(
        School.name,
        School.id,
        func.count(Student.id).label('student_count')
    ).join(Student, School.id == Student.school_id)\
     .group_by(School.id, School.name)\
     .order_by(func.count(Student.id).desc())\
     .limit(10).all()
    
    return {
        "total_schools": total_schools,
        "active_schools": active_schools,
        "pending_schools": pending_schools,
        "total_users": total_users,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "new_schools_30d": new_schools_30d,
        "new_users_30d": new_users_30d,
        "total_revenue": float(total_revenue),
        "monthly_revenue": float(monthly_revenue),
        "top_schools": [
            {
                "name": school.name,
                "id": school.id,
                "student_count": school.student_count
            } for school in top_schools
        ]
    }

# School Management
@router.get("/schools", response_model=List[SchoolResponse])
async def list_all_schools(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status: active, inactive, pending"),
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """List all schools in the system"""
    query = db.query(School)
    
    if status == "active":
        query = query.filter(School.is_active == True, School.is_approved == True)
    elif status == "inactive":
        query = query.filter(School.is_active == False)
    elif status == "pending":
        query = query.filter(School.is_approved == False)
    
    schools = query.offset(skip).limit(limit).all()
    return schools

@router.put("/schools/{school_id}/approve")
async def approve_school(
    school_id: int,
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Approve a pending school"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    school.is_approved = True
    db.commit()
    
    return {"message": "School approved successfully"}

@router.put("/schools/{school_id}/deactivate")
async def deactivate_school(
    school_id: int,
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Deactivate a school"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    school.is_active = False
    db.commit()
    
    return {"message": "School deactivated successfully"}

@router.get("/schools/{school_id}/analytics")
async def get_school_analytics(
    school_id: int,
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific school"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    # School statistics
    total_students = db.query(Student).filter(Student.school_id == school_id).count()
    total_teachers = db.query(Teacher).filter(Teacher.school_id == school_id).count()
    total_users = db.query(User).filter(User.school_id == school_id).count()
    
    # Revenue for this school
    school_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.school_id == school_id,
        Payment.status == 'completed'
    ).scalar() or 0
    
    # Monthly revenue
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    monthly_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.school_id == school_id,
        Payment.status == 'completed',
        Payment.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Attendance rate
    total_attendance = db.query(AttendanceRecord).filter(
        AttendanceRecord.school_id == school_id
    ).count()
    
    present_attendance = db.query(AttendanceRecord).filter(
        AttendanceRecord.school_id == school_id,
        AttendanceRecord.status == 'present'
    ).count()
    
    attendance_rate = (present_attendance / total_attendance * 100) if total_attendance > 0 else 0
    
    return {
        "school_name": school.name,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_users": total_users,
        "total_revenue": float(school_revenue),
        "monthly_revenue": float(monthly_revenue),
        "attendance_rate": round(attendance_rate, 2),
        "is_active": school.is_active,
        "is_approved": school.is_approved,
        "created_at": school.created_at
    }

# System Management
@router.get("/system/health")
async def get_system_health(
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # System statistics
    total_tables = db.execute(text("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)).scalar()
    
    return {
        "database_status": db_status,
        "total_tables": total_tables,
        "server_time": datetime.utcnow().isoformat(),
        "uptime": "System operational"
    }

@router.get("/users/global", response_model=List[UserResponse])
async def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    school_id: Optional[int] = Query(None),
    role: Optional[str] = Query(None),
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """List all users across all schools"""
    query = db.query(User)
    
    if school_id:
        query = query.filter(User.school_id == school_id)
    
    if role:
        query = query.join(User.roles).filter(Role.name == role)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.post("/users/global/create", response_model=UserResponse)
async def create_global_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Create a user for any school (super admin only)"""
    from services.auth import get_password_hash
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_name=user_data.middle_name,
        phone=user_data.phone,
        address=user_data.address,
        hashed_password=hashed_password,
        is_verified=True,  # Super admin created users are auto-verified
        is_approved=True,  # Super admin created users are auto-approved
        school_id=user_data.school_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Assign roles if specified
    if hasattr(user_data, 'role_ids') and user_data.role_ids:
        for role_id in user_data.role_ids:
            role = db.query(Role).filter(Role.id == role_id).first()
            if role:
                new_user.roles.append(role)
        db.commit()
    
    return new_user

@router.get("/analytics/global")
async def get_global_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Get global system analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # User growth
    new_users = db.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= start_date)\
     .group_by(func.date(User.created_at))\
     .order_by(func.date(User.created_at)).all()
    
    # School growth
    new_schools = db.query(
        func.date(School.created_at).label('date'),
        func.count(School.id).label('count')
    ).filter(School.created_at >= start_date)\
     .group_by(func.date(School.created_at))\
     .order_by(func.date(School.created_at)).all()
    
    # Revenue trends
    revenue_trends = db.query(
        func.date(Payment.created_at).label('date'),
        func.sum(Payment.amount).label('revenue')
    ).filter(
        Payment.created_at >= start_date,
        Payment.status == 'completed'
    ).group_by(func.date(Payment.created_at))\
     .order_by(func.date(Payment.created_at)).all()
    
    return {
        "period_days": days,
        "user_growth": [
            {"date": str(row.date), "count": row.count} 
            for row in new_users
        ],
        "school_growth": [
            {"date": str(row.date), "count": row.count} 
            for row in new_schools
        ],
        "revenue_trends": [
            {"date": str(row.date), "revenue": float(row.revenue or 0)} 
            for row in revenue_trends
        ]
    }

@router.delete("/schools/{school_id}")
async def delete_school(
    school_id: int,
    confirm: bool = Query(False, description="Confirm deletion"),
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """Delete a school (super admin only, with confirmation)"""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="School deletion requires confirmation. Add ?confirm=true to the request."
        )
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    # This would typically involve cascading deletes or data archival
    # For now, just mark as inactive
    school.is_active = False
    school.is_approved = False
    db.commit()
    
    return {"message": f"School '{school.name}' has been deactivated"}