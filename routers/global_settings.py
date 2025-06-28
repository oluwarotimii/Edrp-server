from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.global_settings import GlobalSetting
from models.user import User
from schemas.global_settings import GlobalSetting as GlobalSettingSchema, GlobalSettingUpdate
from utils.dependencies import get_current_user, require_permission
from utils.exceptions import NotFoundException

router = APIRouter()

@router.get("/global-settings", response_model=List[GlobalSettingSchema])
async def get_global_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all global settings"""
    require_permission("global_settings:view")(current_user)
    settings = db.query(GlobalSetting).all()
    return settings

@router.put("/global-settings/{key}", response_model=GlobalSettingSchema)
async def update_global_setting(
    key: str,
    setting_update: GlobalSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a global setting by key"""
    require_permission("global_settings:update")(current_user)
    
    setting = db.query(GlobalSetting).filter(GlobalSetting.key == key).first()
    if not setting:
        raise NotFoundException(f"Global setting with key '{key}' not found")
    
    for field, value in setting_update.dict(exclude_unset=True).items():
        setattr(setting, field, value)
    
    db.commit()
    db.refresh(setting)
    
    return setting