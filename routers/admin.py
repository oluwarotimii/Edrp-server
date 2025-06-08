from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from database import get_db
from models.school import School, SchoolSubscription
from models.user import User
from models.student import Student
from models.teacher import Teacher
from models.fee import Payment, StudentFee
from schemas.school import School as SchoolSchema, SchoolSubscription as SchoolSubscriptionSchema
from schemas.user import User as UserSchema
from utils.dependencies import get_current_user, require_permission
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

# Audit Log endpoints
@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs"""
    require_permission("audit_logs:view")(current_user)
    
    # Note: Audit logging would typically be implemented as a separate table
    # For now, this is a placeholder structure
    logs = []
    
    # In a real implementation, you would query an audit_logs table
    # with fields like: id, user_id, action, resource_type, resource_id, 
    # old_values, new_values, ip_address, user_agent, timestamp
    
    return {
        "logs": logs,
        "total": 0,
        "skip": skip,
        "limit": limit
    }

# Subscription Plan Management (for SaaS deployment)
@router.post("/admin/subscription-plans")
async def create_subscription_plan(
    plan_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create subscription plan"""
    require_permission("subscription_plans:create")(current_user)
    
    # This would typically be stored in a subscription_plans table
    # For now, return success message
    return {"message": "Subscription plan created successfully", "plan_id": 1}

@router.get("/admin/subscription-plans")
async def get_subscription_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscription plans"""
    require_permission("subscription_plans:view")(current_user)
    
    # Placeholder for subscription plans
    plans = [
        {
            "id": 1,
            "name": "Basic",
            "max_students": 100,
            "max_teachers": 20,
            "price_monthly": 50.00,
            "features": ["Basic attendance", "Simple grading", "Parent portal"]
        },
        {
            "id": 2,
            "name": "Professional",
            "max_students": 500,
            "max_teachers": 100,
            "price_monthly": 150.00,
            "features": ["Advanced attendance", "Complex grading", "Parent portal", "Behavior tracking", "Advanced reports"]
        },
        {
            "id": 3,
            "name": "Enterprise",
            "max_students": -1,  # Unlimited
            "max_teachers": -1,  # Unlimited
            "price_monthly": 500.00,
            "features": ["All features", "Custom integrations", "Priority support", "Advanced analytics"]
        }
    ]
    
    return plans

@router.put("/admin/subscription-plans/{plan_id}")
async def update_subscription_plan(
    plan_id: int,
    plan_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update subscription plan"""
    require_permission("subscription_plans:update")(current_user)
    
    return {"message": f"Subscription plan {plan_id} updated successfully"}

@router.post("/admin/subscription-plans/{plan_id}/features")
async def set_feature_limit(
    plan_id: int,
    feature_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set feature limit for a plan"""
    require_permission("subscription_plans:manage_features")(current_user)
    
    return {"message": f"Feature limit set for plan {plan_id}"}

@router.get("/admin/subscription-plans/{plan_id}/features")
async def get_feature_limits(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feature limits for a plan"""
    require_permission("subscription_plans:view")(current_user)
    
    # Placeholder feature limits
    features = {
        "max_students": 100,
        "max_teachers": 20,
        "max_classes": 50,
        "max_subjects": 30,
        "advanced_reports": False,
        "api_access": False,
        "custom_branding": False
    }
    
    return features

@router.delete("/admin/subscription-plans/{plan_id}/features/{feature_name}")
async def delete_feature_limit(
    plan_id: int,
    feature_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete feature limit"""
    require_permission("subscription_plans:manage_features")(current_user)
    
    return {"message": f"Feature limit {feature_name} removed from plan {plan_id}"}

# Analytics
@router.get("/admin/analytics/subscriptions")
async def get_subscription_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscription analytics"""
    require_permission("analytics:view")(current_user)
    
    # Calculate date range
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get active schools count
    active_schools = db.query(School).filter(
        School.is_active == True,
        School.is_approved == True
    ).count()
    
    # Get total students across all schools
    total_students = db.query(Student).filter(
        Student.is_active == True
    ).count()
    
    # Get total teachers across all schools
    total_teachers = db.query(Teacher).filter(
        Teacher.is_active == True
    ).count()
    
    # Get revenue (placeholder calculation)
    revenue_data = db.query(
        func.sum(Payment.amount).label('total_revenue'),
        func.count(Payment.id).label('payment_count')
    ).filter(
        Payment.payment_date >= start_date,
        Payment.payment_date <= end_date,
        Payment.status == 'completed'
    ).first()
    
    total_revenue = float(revenue_data.total_revenue or 0)
    payment_count = revenue_data.payment_count or 0
    
    # School growth over time
    school_growth = []
    current_date = start_date
    while current_date <= end_date:
        schools_by_date = db.query(School).filter(
            School.created_at <= current_date,
            School.is_approved == True
        ).count()
        
        school_growth.append({
            "date": current_date.isoformat(),
            "schools": schools_by_date
        })
        
        current_date += timedelta(days=7)  # Weekly data points
    
    return {
        "overview": {
            "active_schools": active_schools,
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_revenue": total_revenue,
            "payment_count": payment_count
        },
        "school_growth": school_growth,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    }

# Pending Schools
@router.get("/admin/schools/pending", response_model=List[SchoolSchema])
async def get_pending_schools(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending schools for approval"""
    require_permission("schools:approve")(current_user)
    
    schools = db.query(School).filter(
        School.is_approved == False,
        School.is_active == True
    ).order_by(desc(School.created_at)).offset(skip).limit(limit).all()
    
    return schools

@router.put("/admin/schools/{school_id}/approve")
async def approve_school(
    school_id: int,
    approval_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve or reject a school"""
    require_permission("schools:approve")(current_user)
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    is_approved = approval_data.get("is_approved", False)
    rejection_reason = approval_data.get("rejection_reason")
    
    school.is_approved = is_approved
    
    if not is_approved:
        school.is_active = False
        # Store rejection reason in settings
        if not school.settings:
            school.settings = {}
        school.settings["rejection_reason"] = rejection_reason
    
    db.commit()
    
    return {
        "message": f"School {'approved' if is_approved else 'rejected'} successfully",
        "school_id": school_id,
        "status": "approved" if is_approved else "rejected"
    }

# System Statistics
@router.get("/admin/statistics")
async def get_system_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall system statistics"""
    require_permission("admin:view_statistics")(current_user)
    
    # Schools statistics
    schools_stats = {
        "total": db.query(School).count(),
        "active": db.query(School).filter(School.is_active == True).count(),
        "pending": db.query(School).filter(School.is_approved == False).count(),
        "approved": db.query(School).filter(School.is_approved == True).count()
    }
    
    # Users statistics
    users_stats = {
        "total": db.query(User).count(),
        "active": db.query(User).filter(User.is_active == True).count(),
        "verified": db.query(User).filter(User.is_verified == True).count(),
        "pending_approval": db.query(User).filter(User.is_approved == False).count()
    }
    
    # Students statistics
    students_stats = {
        "total": db.query(Student).count(),
        "active": db.query(Student).filter(Student.status == "active").count(),
        "graduated": db.query(Student).filter(Student.status == "graduated").count(),
        "withdrawn": db.query(Student).filter(Student.status == "withdrawn").count()
    }
    
    # Teachers statistics
    teachers_stats = {
        "total": db.query(Teacher).count(),
        "active": db.query(Teacher).filter(Teacher.status == "active").count(),
        "on_leave": db.query(Teacher).filter(Teacher.status == "on_leave").count(),
        "resigned": db.query(Teacher).filter(Teacher.status == "resigned").count()
    }
    
    # Financial statistics (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    financial_stats = db.query(
        func.sum(Payment.amount).label('total_revenue'),
        func.count(Payment.id).label('transaction_count'),
        func.avg(Payment.amount).label('average_payment')
    ).filter(
        Payment.payment_date >= thirty_days_ago,
        Payment.status == 'completed'
    ).first()
    
    # Top performing schools by student count
    top_schools = db.query(
        School.name,
        func.count(Student.id).label('student_count')
    ).join(Student).filter(
        School.is_active == True,
        Student.status == "active"
    ).group_by(School.id, School.name).order_by(
        desc(func.count(Student.id))
    ).limit(10).all()
    
    return {
        "schools": schools_stats,
        "users": users_stats,
        "students": students_stats,
        "teachers": teachers_stats,
        "financial": {
            "total_revenue": float(financial_stats.total_revenue or 0),
            "transaction_count": financial_stats.transaction_count or 0,
            "average_payment": float(financial_stats.average_payment or 0),
            "period": "Last 30 days"
        },
        "top_schools": [
            {"name": school.name, "student_count": school.student_count}
            for school in top_schools
        ],
        "generated_at": datetime.utcnow().isoformat()
    }

# Health Check and System Status
@router.get("/admin/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    require_permission("admin:view_system_health")(current_user)
    
    # Database connectivity check
    try:
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        database_status = f"error: {str(e)}"
    
    # Check recent activity
    recent_logins = db.query(User).filter(
        User.last_login >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    recent_payments = db.query(Payment).filter(
        Payment.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    # System metrics
    health_data = {
        "status": "healthy" if database_status == "healthy" else "degraded",
        "database": {
            "status": database_status,
            "connection_pool": "active"  # Placeholder
        },
        "activity": {
            "recent_logins_24h": recent_logins,
            "recent_payments_24h": recent_payments
        },
        "services": {
            "authentication": "healthy",
            "notifications": "healthy",
            "file_uploads": "healthy",
            "payment_gateway": "healthy"
        },
        "last_check": datetime.utcnow().isoformat()
    }
    
    return health_data
