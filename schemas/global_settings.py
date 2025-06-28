from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GlobalSettingBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class GlobalSettingCreate(GlobalSettingBase):
    pass

class GlobalSettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None

class GlobalSetting(GlobalSettingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True