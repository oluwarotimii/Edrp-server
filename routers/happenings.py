from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.communication import Happening
from models.user import User
from schemas.communication import (
    Happening as HappeningSchema, HappeningCreate, HappeningUpdate
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException
from services.notifications import NotificationService

router = APIRouter()

@router.post("/happenings", response_model=HappeningSchema)
async def create_happening(
    happening: HappeningCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new school happening/event"""
    require_permission("happenings:create")(current_user)
    
    db_happening = Happening(
        title=happening.title,
        description=happening.description,
        category=happening.category,
        target_audience=happening.target_audience,
        event_date=happening.event_date,
        location=happening.location,
        school_id=school_id
    )
    
    db.add(db_happening)
    db.commit()
    db.refresh(db_happening)
    
    return db_happening

@router.get("/happenings", response_model=List[HappeningSchema])
async def get_happenings(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None),
    target_audience: Optional[str] = Query(None),
    published_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get all school happenings with filters"""
    query = db.query(Happening).filter(Happening.school_id == school_id)
    
    # Filter by published status unless user has admin permissions
    if published_only:
        try:
            require_permission("happenings:view_unpublished")(current_user)
        except:
            query = query.filter(Happening.is_published == True)
    
    if category:
        query = query.filter(Happening.category == category)
    
    if target_audience:
        query = query.filter(
            (Happening.target_audience == target_audience) | 
            (Happening.target_audience == "all")
        )
    
    happenings = query.order_by(Happening.event_date.desc(), Happening.created_at.desc()).offset(skip).limit(limit).all()
    return happenings

@router.get("/happenings/{happening_id}", response_model=HappeningSchema)
async def get_happening(
    happening_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get details of a specific happening"""
    happening = db.query(Happening).filter(
        Happening.id == happening_id,
        Happening.school_id == school_id
    ).first()
    
    if not happening:
        raise NotFoundException("Happening not found")
    
    # Check if unpublished and user has permission
    if not happening.is_published:
        require_permission("happenings:view_unpublished")(current_user)
    
    return happening

@router.put("/happenings/{happening_id}", response_model=HappeningSchema)
async def update_happening(
    happening_id: int,
    happening_update: HappeningUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update details of a specific happening"""
    require_permission("happenings:update")(current_user)
    
    happening = db.query(Happening).filter(
        Happening.id == happening_id,
        Happening.school_id == school_id
    ).first()
    
    if not happening:
        raise NotFoundException("Happening not found")
    
    # Track if we're publishing for the first time
    was_published = happening.is_published
    
    # Update fields
    for field, value in happening_update.dict(exclude_unset=True).items():
        setattr(happening, field, value)
    
    # Set publication details if publishing
    if happening_update.is_published and not was_published:
        happening.published_by = current_user.id
        happening.published_at = datetime.utcnow()
        
        # Send notifications to relevant users
        if happening.target_audience:
            notification_service = NotificationService()
            await notification_service.send_happening_notification(
                happening_id=happening.id,
                title=happening.title,
                category=happening.category,
                target_audience=happening.target_audience,
                school_id=school_id,
                db=db
            )
    
    db.commit()
    db.refresh(happening)
    
    return happening

@router.delete("/happenings/{happening_id}")
async def delete_happening(
    happening_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Delete a specific happening"""
    require_permission("happenings:delete")(current_user)
    
    happening = db.query(Happening).filter(
        Happening.id == happening_id,
        Happening.school_id == school_id
    ).first()
    
    if not happening:
        raise NotFoundException("Happening not found")
    
    db.delete(happening)
    db.commit()
    
    return {"message": "Happening deleted successfully"}

@router.get("/happenings/categories")
async def get_happening_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get predefined categories for happenings"""
    categories = [
        {
            "name": "event",
            "display_name": "Event",
            "description": "School events and activities"
        },
        {
            "name": "announcement",
            "display_name": "Announcement",
            "description": "General announcements and notices"
        },
        {
            "name": "incident",
            "display_name": "Incident",
            "description": "Security or safety incidents"
        },
        {
            "name": "academic",
            "display_name": "Academic",
            "description": "Academic-related news and updates"
        },
        {
            "name": "sports",
            "display_name": "Sports",
            "description": "Sports activities and competitions"
        },
        {
            "name": "cultural",
            "display_name": "Cultural",
            "description": "Cultural events and celebrations"
        },
        {
            "name": "emergency",
            "display_name": "Emergency",
            "description": "Emergency notifications and alerts"
        },
        {
            "name": "maintenance",
            "display_name": "Maintenance",
            "description": "Facility maintenance and closures"
        }
    ]
    
    return categories

@router.post("/happenings/categories")
async def create_happening_category(
    category_data: dict,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new happening category"""
    require_permission("happenings:manage_categories")(current_user)
    
    # In a full implementation, this would store custom categories
    # For now, return success with the provided data
    return {
        "message": "Category created successfully",
        "category": category_data
    }

# Bulk operations
@router.post("/happenings/bulk-publish")
async def bulk_publish_happenings(
    happening_ids: List[int],
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Bulk publish multiple happenings"""
    require_permission("happenings:publish")(current_user)
    
    happenings = db.query(Happening).filter(
        Happening.id.in_(happening_ids),
        Happening.school_id == school_id,
        Happening.is_published == False
    ).all()
    
    published_count = 0
    for happening in happenings:
        happening.is_published = True
        happening.published_by = current_user.id
        happening.published_at = datetime.utcnow()
        published_count += 1
        
        # Send notifications
        if happening.target_audience:
            notification_service = NotificationService()
            await notification_service.send_happening_notification(
                happening_id=happening.id,
                title=happening.title,
                category=happening.category,
                target_audience=happening.target_audience,
                school_id=school_id,
                db=db
            )
    
    db.commit()
    
    return {
        "message": f"Successfully published {published_count} happenings",
        "published_count": published_count
    }

# Statistics
@router.get("/happenings/statistics")
async def get_happenings_statistics(
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get happenings statistics"""
    require_permission("happenings:view_statistics")(current_user)
    
    # Count by category
    from sqlalchemy import func
    category_stats = db.query(
        Happening.category,
        func.count(Happening.id).label('count')
    ).filter(
        Happening.school_id == school_id
    ).group_by(Happening.category).all()
    
    # Count by status
    total_happenings = db.query(Happening).filter(Happening.school_id == school_id).count()
    published_happenings = db.query(Happening).filter(
        Happening.school_id == school_id,
        Happening.is_published == True
    ).count()
    draft_happenings = total_happenings - published_happenings
    
    # Recent activity
    from datetime import timedelta
    recent_happenings = db.query(Happening).filter(
        Happening.school_id == school_id,
        Happening.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    return {
        "overview": {
            "total_happenings": total_happenings,
            "published": published_happenings,
            "drafts": draft_happenings,
            "recent_30_days": recent_happenings
        },
        "by_category": [
            {"category": stat.category, "count": stat.count}
            for stat in category_stats
        ]
    }
