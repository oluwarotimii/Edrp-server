"""
Subdomain management endpoints for schools.

This module provides endpoints for managing school subdomains, including checking
availability and updating subdomains.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from models.school import School
from schemas.school import SubdomainBase, SchoolUpdate
from utils.dependencies import get_current_user, require_permission
from utils.exceptions import ValidationException

router = APIRouter(prefix="/api/v1/subdomains", tags=["subdomains"])
logger = logging.getLogger(__name__)

@router.get("/check-availability")
async def check_subdomain_availability(
    subdomain: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Check if a subdomain is available for use.
    
    Args:
        subdomain: The subdomain to check
        
    Returns:
        dict: Object indicating if the subdomain is available and any suggestions if taken
    """
    from ..models.school import School as SchoolModel
    
    try:
        # Basic validation
        SubdomainBase.validate_subdomain(subdomain)
        
        # Check if subdomain is already taken
        exists = db.query(
            db.query(School)
            .filter(School.subdomain == subdomain.lower())
            .exists()
        ).scalar()
        
        if exists:
            return {
                "available": False,
                "message": f"Subdomain '{subdomain}' is already taken"
            }
            
        return {
            "available": True,
            "message": f"Subdomain '{subdomain}' is available"
        }
        
    except ValueError as e:
        raise ValidationException(str(e))
    except Exception as e:
        logger.error(f"Error checking subdomain availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking subdomain availability"
        )

@router.get("/suggest")
async def suggest_subdomains(
    name: str,
    limit: int = 5,
    db: Session = Depends(get_db)
) -> dict:
    """
    Generate suggested subdomains based on a school name.
    
    Args:
        name: The school name to generate suggestions from
        limit: Maximum number of suggestions to return (default: 5)
        
    Returns:
        dict: List of suggested subdomains
    """
    from ..models.school import School as SchoolModel
    
    try:
        if not name or len(name.strip()) < 2:
            return {"suggestions": []}
            
        base_subdomain = SchoolModel.generate_subdomain(name)
        suggestions = [base_subdomain]
        
        # Generate variations if needed
        for i in range(1, limit):
            suggestion = f"{base_subdomain}-{i}"
            suggestions.append(suggestion)
            
        # Filter out any that are already taken
        available_suggestions = []
        for suggestion in suggestions:
            exists = db.query(
                db.query(School)
                .filter(School.subdomain == suggestion)
                .exists()
            ).scalar()
            
            if not exists:
                available_suggestions.append(suggestion)
                
            if len(available_suggestions) >= limit:
                break
                
        return {"suggestions": available_suggestions}
        
    except Exception as e:
        logger.error(f"Error generating subdomain suggestions: {str(e)}")
        return {"suggestions": []}

@router.patch("/{school_id}/update")
async def update_school_subdomain(
    school_id: int,
    subdomain_update: SubdomainBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Update a school's subdomain.
    
    Args:
        school_id: ID of the school to update
        subdomain_update: New subdomain value
        current_user: Currently authenticated user
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If the school is not found, user is not authorized,
                     or the subdomain is invalid or already taken
    """
    from ..models.school import School as SchoolModel
    
    try:
        # Get the school
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            raise NotFoundException("School not found")
            
        # Check permissions
        if not current_user.is_superuser and not current_user.is_school_admin(school_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this school's subdomain"
            )
            
        # Validate the new subdomain
        new_subdomain = subdomain_update.subdomain.lower().strip()
        
        # Check if the subdomain is actually changing
        if school.subdomain == new_subdomain:
            return {"message": "Subdomain updated successfully"}
            
        # Check if the subdomain is available
        exists = db.query(
            db.query(School)
            .filter(School.subdomain == new_subdomain)
            .filter(School.id != school_id)
            .exists()
        ).scalar()
        
        if exists:
            raise ValidationException(f"Subdomain '{new_subdomain}' is already taken")
            
        # Update the subdomain
        school.subdomain = new_subdomain
        db.commit()
        
        # Invalidate any caches if needed
        # invalidate_school_cache(school_id)
        
        return {"message": "Subdomain updated successfully"}
        
    except HTTPException:
        raise
    except ValidationException as e:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating school subdomain: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the subdomain"
        )

def register_subdomain_routes(app):
    """Register subdomain routes with the FastAPI app."""
    app.include_router(router)
    
    @app.middleware("http")
    async def subdomain_middleware(request, call_next):
        """
        Middleware to handle subdomain-based routing.
        
        Extracts the subdomain from the request and makes it available
        in the request state for use in route handlers.
        """
        from urllib.parse import urlparse
        
        # Get the host header
        host_header = request.headers.get("host", "")
        
        # Parse the host to get the domain parts
        domain_parts = host_header.replace("https://", "").replace("http://", "").split(".")
        
        # If we have at least 3 parts (subdomain.domain.tld) or 
        # 2 parts in development (subdomain.localhost)
        if len(domain_parts) >= 2:
            # The subdomain is the first part
            subdomain = domain_parts[0].lower()
            
            # Skip common subdomains that aren't school-specific
            if subdomain not in ["www", "api", "app", "admin"]:
                request.state.subdomain = subdomain
        
        # Continue processing the request
        response = await call_next(request)
        return response
