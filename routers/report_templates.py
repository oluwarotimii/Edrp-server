from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.school import ReportTemplate
from models.user import User
from schemas.school import ReportTemplate as ReportTemplateSchema, ReportTemplateCreate, ReportTemplateUpdate
from utils.dependencies import get_current_user, require_permission

router = APIRouter()

@router.post("/report-templates", response_model=ReportTemplateSchema, status_code=status.HTTP_201_CREATED)
def create_report_template(
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Report Template. Super Admin only.
    """
    require_permission("super_admin")(current_user)

    db_template = ReportTemplate(**template_data.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/report-templates", response_model=List[ReportTemplateSchema])
def get_all_report_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of all Report Templates.
    """
    require_permission("super_admin")(current_user)
    return db.query(ReportTemplate).all()

@router.get("/report-templates/{template_id}", response_model=ReportTemplateSchema)
def get_report_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single Report Template by ID.
    """
    require_permission("super_admin")(current_user)
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report Template not found")
    return template

@router.put("/report-templates/{template_id}", response_model=ReportTemplateSchema)
def update_report_template(
    template_id: int,
    template_data: ReportTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a Report Template. Super Admin only.
    """
    require_permission("super_admin")(current_user)

    db_template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report Template not found")

    for key, value in template_data.dict(exclude_unset=True).items():
        setattr(db_template, key, value)

    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/report-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a Report Template. Super Admin only.
    """
    require_permission("super_admin")(current_user)

    db_template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report Template not found")

    # Add check if template is in use before deleting
    # For now, assuming it's safe to delete if not explicitly linked

    db.delete(db_template)
    db.commit()
