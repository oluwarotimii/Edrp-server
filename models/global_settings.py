from sqlalchemy import Column, Integer, String, Float, DateTime, func
from .base import BaseModel

class GlobalSetting(BaseModel):
    __tablename__ = "global_settings"
    
    key = Column(String(255), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(500))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())