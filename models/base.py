from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.sql import func

# Import the centralized Base from database.py
from database import Base

class BaseModel(Base):
    """Base model with common fields for all tables"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class TenantBaseModel(BaseModel):
    """Base model for multi-tenant tables"""
    __abstract__ = True
    
    # All tenant models will have school_id for data isolation
    school_id = Column(Integer, index=True, nullable=False)
