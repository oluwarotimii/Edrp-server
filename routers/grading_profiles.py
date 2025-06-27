from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.academic import GradingProfile
from models.user import User
from schemas.academic import GradingProfile as GradingProfileSchema, GradingProfileCreate, GradingProfileUpdate
from utils.dependencies import get_current_user, require_permission

router = APIRouter()

@router.post("/grading-profiles", response_model=GradingProfileSchema, status_code=status.HTTP_201_CREATED)
def create_grading_profile(
    profile_data: GradingProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Grading Profile. Super Admin only.
    """
    require_permission("super_admin")(current_user)

    db_profile = GradingProfile(**profile_data.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.get("/grading-profiles", response_model=List[GradingProfileSchema])
def get_all_grading_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of all Grading Profiles.
    """
    # Allow all authenticated users to see the profiles to choose from
    return db.query(GradingProfile).all()

@router.get("/grading-profiles/{profile_id}", response_model=GradingProfileSchema)
def get_grading_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single Grading Profile by ID.
    """
    profile = db.query(GradingProfile).filter(GradingProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading Profile not found")
    return profile

@router.put("/grading-profiles/{profile_id}", response_model=GradingProfileSchema)
def update_grading_profile(
    profile_id: int,
    profile_data: GradingProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a Grading Profile. Super Admin only.
    """
    require_permission("super_admin")(current_user)

    db_profile = db.query(GradingProfile).filter(GradingProfile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading Profile not found")

    for key, value in profile_data.dict(exclude_unset=True).items():
        setattr(db_profile, key, value)

    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.delete("/grading-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grading_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a Grading Profile. Super Admin only.
    """
    require_permission("super_admin")(current_user)

    db_profile = db.query(GradingProfile).filter(GradingProfile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grading Profile not found")

    if db_profile.schools:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete this profile as it is currently in use by one or more schools."
        )

    db.delete(db_profile)
    db.commit()
