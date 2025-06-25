from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models.subscription import SubscriptionPlan
from models.school import SchoolSubscription, School
from models.user import User
from schemas.subscription import (
    SubscriptionPlanCreate, SubscriptionPlanUpdate, SubscriptionPlanResponse,
    SchoolSubscriptionCreate, SchoolSubscriptionResponse, SubscriptionStatusResponse
)
from utils.dependencies import get_current_user, require_permission
from utils.exceptions import NotFoundException, ValidationException
from services.paystack import PaystackService

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])

# Subscription Plan Management (Super Admin)
@router.post("/plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription_plan(
    plan_data: SubscriptionPlanCreate,
    current_user: User = Depends(require_permission("subscription_plans:create")),
    db: Session = Depends(get_db)
):
    """Create a new subscription plan (Super Admin only)"""
    # Check if plan name already exists
    existing_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == plan_data.name
    ).first()
    
    if existing_plan:
        raise ValidationException("A plan with this name already exists")
    
    # Create the plan in Paystack
    paystack = PaystackService()
    
    # Only create Paystack plan if not a free plan
    paystack_plan_code = None
    if plan_data.price_monthly > 0:
        plan_code = f"edrp_{plan_data.name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"
        
        # Create monthly plan
        monthly_plan = await paystack.create_plan(
            name=f"{plan_data.name} (Monthly)",
            amount=int(plan_data.price_monthly * 100),  # Convert to kobo
            interval="monthly",
            plan_code=plan_code + "_monthly"
        )
        
        if not monthly_plan.get("status"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create Paystack plan: {monthly_plan.get('message')}"
            )
        
        paystack_plan_code = monthly_plan["data"]["plan_code"]
    
    # Create the plan in our database
    db_plan = SubscriptionPlan(
        **plan_data.dict(exclude={"price_yearly"}),
        paystack_plan_code=paystack_plan_code
    )
    
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    
    return db_plan

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_subscription_plans(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all subscription plans"""
    query = db.query(SubscriptionPlan)
    
    if not include_inactive:
        query = query.filter(SubscriptionPlan.is_active == True)
    
    return query.order_by(SubscriptionPlan.price_monthly).all()

@router.get("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get subscription plan details"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise NotFoundException("Subscription plan not found")
    return plan

@router.put("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_subscription_plan(
    plan_id: int,
    plan_data: SubscriptionPlanUpdate,
    current_user: User = Depends(require_permission("subscription_plans:update")),
    db: Session = Depends(get_db)
):
    """Update a subscription plan (Super Admin only)"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise NotFoundException("Subscription plan not found")
    
    # Don't allow updating price if there are active subscriptions
    if plan_data.price_monthly is not None and plan_data.price_monthly != plan.price_monthly:
        active_subscriptions = db.query(SchoolSubscription).filter(
            SchoolSubscription.plan_id == plan_id,
            SchoolSubscription.status == "active"
        ).count()
        
        if active_subscriptions > 0:
            raise ValidationException("Cannot update price for a plan with active subscriptions")
    
    # Update plan details
    for field, value in plan_data.dict(exclude_unset=True).items():
        setattr(plan, field, value)
    
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    
    return plan

@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription_plan(
    plan_id: int,
    current_user: User = Depends(require_permission("subscription_plans:delete")),
    db: Session = Depends(get_db)
):
    """Delete a subscription plan (Super Admin only)"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise NotFoundException("Subscription plan not found")
    
    # Don't allow deleting plans with active subscriptions
    active_subscriptions = db.query(SchoolSubscription).filter(
        SchoolSubscription.plan_id == plan_id,
        SchoolSubscription.status == "active"
    ).count()
    
    if active_subscriptions > 0:
        raise ValidationException("Cannot delete a plan with active subscriptions")
    
    # Instead of deleting, mark as inactive
    plan.is_active = False
    db.commit()
    
    return None

# School Subscription Management
@router.get("/schools/{school_id}", response_model=SubscriptionStatusResponse)
async def get_school_subscription(
    school_id: int,
    current_user: User = Depends(require_permission("subscriptions:view")),
    db: Session = Depends(get_db)
):
    """Get a school's subscription status"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise NotFoundException("School not found")
    
    if not school.subscription:
        raise NotFoundException("No active subscription found for this school")
    
    # Get current usage
    student_count = db.query(Student).filter(Student.school_id == school_id).count()
    teacher_count = db.query(Teacher).filter(Teacher.school_id == school_id).count()
    
    # Calculate days remaining if end_date is set
    days_remaining = None
    if school.subscription.end_date:
        days_remaining = (school.subscription.end_date - datetime.utcnow()).days
        days_remaining = max(0, days_remaining)  # Don't show negative days
    
    return {
        "is_active": school.subscription.is_active,
        "status": school.subscription.status,
        "plan_name": school.subscription.plan.name,
        "start_date": school.subscription.start_date,
        "end_date": school.subscription.end_date,
        "days_remaining": days_remaining,
        "max_students": school.subscription.plan.max_students,
        "max_teachers": school.subscription.plan.max_teachers,
        "max_storage_mb": school.subscription.plan.max_storage_mb,
        "current_usage": {
            "students": student_count,
            "teachers": teacher_count,
            "storage_mb": 0  # TODO: Implement storage tracking
        }
    }

# Webhook handler for Paystack events
@router.post("/webhooks/paystack")
async def handle_paystack_webhook(
    payload: dict,
    db: Session = Depends(get_db)
):
    """Handle Paystack webhook events for subscriptions"""
    # Verify the webhook signature (implement this based on Paystack docs)
    # ...
    
    event = payload.get("event")
    data = payload.get("data", {})
    
    if event == "subscription.create":
        # Handle new subscription
        subscription_code = data.get("subscription_code")
        customer_code = data.get("customer", {}).get("customer_code")
        
        # Update the school subscription with Paystack details
        subscription = db.query(SchoolSubscription).filter(
            SchoolSubscription.paystack_subscription_code == subscription_code
        ).first()
        
        if subscription:
            subscription.status = "active"
            subscription.paystack_customer_code = customer_code
            db.commit()
    
    elif event in ["subscription.disable", "subscription.expiring_cards"]:
        # Handle subscription issues
        subscription_code = data.get("subscription_code")
        
        subscription = db.query(SchoolSubscription).filter(
            SchoolSubscription.paystack_subscription_code == subscription_code
        ).first()
        
        if subscription:
            subscription.status = "inactive"
            db.commit()
    
    return {"status": "success"}
