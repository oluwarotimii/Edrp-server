from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from database import get_db
from models.assessment import AssessmentScheme, AssessmentComponent, GradingScale, Assessment, Score
from models.academic import Subject, Class, Term
from models.student import Student
from models.user import User
from schemas.assessment import (
    AssessmentScheme as AssessmentSchemeSchema, AssessmentSchemeCreate, AssessmentSchemeUpdate,
    AssessmentComponent as AssessmentComponentSchema, AssessmentComponentCreate, AssessmentComponentUpdate,
    GradingScale as GradingScaleSchema, GradingScaleCreate, GradingScaleUpdate,
    Assessment as AssessmentSchema, AssessmentCreate, AssessmentUpdate,
    Score as ScoreSchema, ScoreCreate, ScoreUpdate, BatchScoreCreate,
    SchemeAssignment, StudentResults
)
from utils.dependencies import get_current_user, require_permission, get_current_school
from utils.exceptions import NotFoundException, ValidationException

router = APIRouter()

# Assessment Scheme endpoints
@router.post("/assessment-schemes", response_model=AssessmentSchemeSchema)
async def create_assessment_scheme(
    scheme: AssessmentSchemeCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new assessment scheme"""
    require_permission("assessment_schemes:create")(current_user)
    
    # If this is set as default, unset any existing default
    if scheme.is_default:
        db.query(AssessmentScheme).filter(
            AssessmentScheme.school_id == school_id,
            AssessmentScheme.is_default == True
        ).update({"is_default": False})
    
    db_scheme = AssessmentScheme(
        name=scheme.name,
        description=scheme.description,
        is_default=scheme.is_default,
        school_id=school_id
    )
    
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    
    return db_scheme

@router.get("/assessment-schemes", response_model=List[AssessmentSchemeSchema])
async def get_assessment_schemes(
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get all assessment schemes"""
    require_permission("assessment_schemes:view")(current_user)
    
    schemes = db.query(AssessmentScheme).filter(
        AssessmentScheme.school_id == school_id
    ).all()
    
    return schemes

@router.get("/assessment-schemes/{scheme_id}", response_model=AssessmentSchemeSchema)
async def get_assessment_scheme(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific assessment scheme"""
    require_permission("assessment_schemes:view")(current_user)
    
    scheme = db.query(AssessmentScheme).filter(
        AssessmentScheme.id == scheme_id,
        AssessmentScheme.school_id == school_id
    ).first()
    
    if not scheme:
        raise NotFoundException("Assessment scheme not found")
    
    return scheme

@router.put("/assessment-schemes/{scheme_id}", response_model=AssessmentSchemeSchema)
async def update_assessment_scheme(
    scheme_id: int,
    scheme_update: AssessmentSchemeUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update an assessment scheme"""
    require_permission("assessment_schemes:update")(current_user)
    
    scheme = db.query(AssessmentScheme).filter(
        AssessmentScheme.id == scheme_id,
        AssessmentScheme.school_id == school_id
    ).first()
    
    if not scheme:
        raise NotFoundException("Assessment scheme not found")
    
    # If setting as default, unset other defaults
    if scheme_update.is_default:
        db.query(AssessmentScheme).filter(
            AssessmentScheme.school_id == school_id,
            AssessmentScheme.id != scheme_id,
            AssessmentScheme.is_default == True
        ).update({"is_default": False})
    
    # Update fields
    for field, value in scheme_update.dict(exclude_unset=True).items():
        setattr(scheme, field, value)
    
    db.commit()
    db.refresh(scheme)
    
    return scheme

@router.delete("/assessment-schemes/{scheme_id}")
async def delete_assessment_scheme(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Delete an assessment scheme"""
    require_permission("assessment_schemes:delete")(current_user)
    
    scheme = db.query(AssessmentScheme).filter(
        AssessmentScheme.id == scheme_id,
        AssessmentScheme.school_id == school_id
    ).first()
    
    if not scheme:
        raise NotFoundException("Assessment scheme not found")
    
    # Check if scheme is in use
    components_count = db.query(AssessmentComponent).filter(
        AssessmentComponent.scheme_id == scheme_id
    ).count()
    
    if components_count > 0:
        raise ValidationException("Cannot delete scheme with existing components")
    
    db.delete(scheme)
    db.commit()
    
    return {"message": "Assessment scheme deleted successfully"}

# Assessment Component endpoints
@router.post("/assessment-schemes/{scheme_id}/components", response_model=AssessmentComponentSchema)
async def add_component_to_scheme(
    scheme_id: int,
    component: AssessmentComponentCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Add a component to an assessment scheme"""
    require_permission("assessment_schemes:manage_components")(current_user)
    
    # Verify scheme exists
    scheme = db.query(AssessmentScheme).filter(
        AssessmentScheme.id == scheme_id,
        AssessmentScheme.school_id == school_id
    ).first()
    
    if not scheme:
        raise NotFoundException("Assessment scheme not found")
    
    # Check total weight doesn't exceed 100%
    existing_weights = db.query(AssessmentComponent).filter(
        AssessmentComponent.scheme_id == scheme_id
    ).all()
    
    total_weight = sum(comp.weight_percentage for comp in existing_weights) + component.weight_percentage
    
    if total_weight > 100:
        raise ValidationException("Total component weights cannot exceed 100%")
    
    db_component = AssessmentComponent(
        scheme_id=scheme_id,
        name=component.name,
        weight_percentage=component.weight_percentage,
        max_score=component.max_score,
        school_id=school_id
    )
    
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    
    return db_component

@router.get("/assessment-schemes/{scheme_id}/components", response_model=List[AssessmentComponentSchema])
async def get_scheme_components(
    scheme_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get all components of a scheme"""
    require_permission("assessment_schemes:view")(current_user)
    
    # Verify scheme exists
    scheme = db.query(AssessmentScheme).filter(
        AssessmentScheme.id == scheme_id,
        AssessmentScheme.school_id == school_id
    ).first()
    
    if not scheme:
        raise NotFoundException("Assessment scheme not found")
    
    components = db.query(AssessmentComponent).filter(
        AssessmentComponent.scheme_id == scheme_id
    ).all()
    
    return components

@router.put("/assessment-schemes/{scheme_id}/components/{component_id}", response_model=AssessmentComponentSchema)
async def update_component(
    scheme_id: int,
    component_id: int,
    component_update: AssessmentComponentUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a component within a scheme"""
    require_permission("assessment_schemes:manage_components")(current_user)
    
    component = db.query(AssessmentComponent).filter(
        AssessmentComponent.id == component_id,
        AssessmentComponent.scheme_id == scheme_id,
        AssessmentComponent.school_id == school_id
    ).first()
    
    if not component:
        raise NotFoundException("Component not found")
    
    # Check weight constraints if updating weight
    if component_update.weight_percentage is not None:
        other_weights = db.query(AssessmentComponent).filter(
            AssessmentComponent.scheme_id == scheme_id,
            AssessmentComponent.id != component_id
        ).all()
        
        total_weight = sum(comp.weight_percentage for comp in other_weights) + component_update.weight_percentage
        
        if total_weight > 100:
            raise ValidationException("Total component weights cannot exceed 100%")
    
    # Update fields
    for field, value in component_update.dict(exclude_unset=True).items():
        setattr(component, field, value)
    
    db.commit()
    db.refresh(component)
    
    return component

@router.delete("/assessment-schemes/{scheme_id}/components/{component_id}")
async def delete_component(
    scheme_id: int,
    component_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Delete a component from a scheme"""
    require_permission("assessment_schemes:manage_components")(current_user)
    
    component = db.query(AssessmentComponent).filter(
        AssessmentComponent.id == component_id,
        AssessmentComponent.scheme_id == scheme_id,
        AssessmentComponent.school_id == school_id
    ).first()
    
    if not component:
        raise NotFoundException("Component not found")
    
    # Check if component is in use
    assessments_count = db.query(Assessment).filter(
        Assessment.component_id == component_id
    ).count()
    
    if assessments_count > 0:
        raise ValidationException("Cannot delete component with existing assessments")
    
    db.delete(component)
    db.commit()
    
    return {"message": "Component deleted successfully"}

# Grading Scale endpoints
@router.post("/grading-scales", response_model=GradingScaleSchema)
async def create_grading_scale(
    grade: GradingScaleCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create grading scale entry"""
    require_permission("grading_scales:create")(current_user)
    
    db_grade = GradingScale(
        grade=grade.grade,
        min_score=grade.min_score,
        max_score=grade.max_score,
        description=grade.description,
        gpa_value=grade.gpa_value,
        school_id=school_id
    )
    
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    
    return db_grade

@router.get("/grading-scales", response_model=List[GradingScaleSchema])
async def get_grading_scales(
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get school's grading scale"""
    require_permission("grading_scales:view")(current_user)
    
    grades = db.query(GradingScale).filter(
        GradingScale.school_id == school_id
    ).order_by(GradingScale.min_score.desc()).all()
    
    return grades

@router.put("/grading-scales/{grade_id}", response_model=GradingScaleSchema)
async def update_grading_scale(
    grade_id: int,
    grade_update: GradingScaleUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a grade level"""
    require_permission("grading_scales:update")(current_user)
    
    grade = db.query(GradingScale).filter(
        GradingScale.id == grade_id,
        GradingScale.school_id == school_id
    ).first()
    
    if not grade:
        raise NotFoundException("Grade not found")
    
    # Update fields
    for field, value in grade_update.dict(exclude_unset=True).items():
        setattr(grade, field, value)
    
    db.commit()
    db.refresh(grade)
    
    return grade

@router.delete("/grading-scales/{grade_id}")
async def delete_grading_scale(
    grade_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Delete a grade level"""
    require_permission("grading_scales:delete")(current_user)
    
    grade = db.query(GradingScale).filter(
        GradingScale.id == grade_id,
        GradingScale.school_id == school_id
    ).first()
    
    if not grade:
        raise NotFoundException("Grade not found")
    
    db.delete(grade)
    db.commit()
    
    return {"message": "Grade deleted successfully"}

# Class/Subject scheme assignment
@router.post("/classes/{class_id}/subjects/{subject_id}/assign-scheme")
async def assign_scheme_to_class_subject(
    class_id: int,
    subject_id: int,
    assignment: SchemeAssignment,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Assign assessment scheme to class/subject combination"""
    require_permission("assessment_schemes:assign")(current_user)
    
    # Verify class and subject exist
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise NotFoundException("Class not found")
    
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.school_id == school_id
    ).first()
    
    if not subject:
        raise NotFoundException("Subject not found")
    
    # Verify scheme exists
    scheme = db.query(AssessmentScheme).filter(
        AssessmentScheme.id == assignment.scheme_id,
        AssessmentScheme.school_id == school_id
    ).first()
    
    if not scheme:
        raise NotFoundException("Assessment scheme not found")
    
    # For now, we'll store this assignment in the class-subject relationship
    # In a more complex system, you might want a dedicated table for this
    
    return {"message": "Scheme assigned successfully", "scheme_id": assignment.scheme_id}

# Assessment endpoints
@router.post("/assessments", response_model=AssessmentSchema)
async def create_assessment(
    assessment: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a new assessment"""
    require_permission("assessments:create")(current_user)
    
    # Verify all referenced entities exist
    subject = db.query(Subject).filter(
        Subject.id == assessment.subject_id,
        Subject.school_id == school_id
    ).first()
    if not subject:
        raise NotFoundException("Subject not found")
    
    class_obj = db.query(Class).filter(
        Class.id == assessment.class_id,
        Class.school_id == school_id
    ).first()
    if not class_obj:
        raise NotFoundException("Class not found")
    
    term = db.query(Term).filter(
        Term.id == assessment.term_id,
        Term.school_id == school_id
    ).first()
    if not term:
        raise NotFoundException("Term not found")
    
    component = db.query(AssessmentComponent).filter(
        AssessmentComponent.id == assessment.component_id,
        AssessmentComponent.school_id == school_id
    ).first()
    if not component:
        raise NotFoundException("Assessment component not found")
    
    db_assessment = Assessment(
        name=assessment.name,
        description=assessment.description,
        subject_id=assessment.subject_id,
        class_id=assessment.class_id,
        term_id=assessment.term_id,
        component_id=assessment.component_id,
        max_score=assessment.max_score,
        date_conducted=assessment.date_conducted,
        instructions=assessment.instructions,
        duration_minutes=assessment.duration_minutes,
        school_id=school_id
    )
    
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    
    return db_assessment

@router.get("/assessments", response_model=List[AssessmentSchema])
async def get_assessments(
    skip: int = 0,
    limit: int = 100,
    subject_id: Optional[int] = Query(None),
    class_id: Optional[int] = Query(None),
    term_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get assessments"""
    require_permission("assessments:view")(current_user)
    
    query = db.query(Assessment).filter(Assessment.school_id == school_id)
    
    if subject_id:
        query = query.filter(Assessment.subject_id == subject_id)
    if class_id:
        query = query.filter(Assessment.class_id == class_id)
    if term_id:
        query = query.filter(Assessment.term_id == term_id)
    
    assessments = query.offset(skip).limit(limit).all()
    return assessments

@router.get("/assessments/{assessment_id}", response_model=AssessmentSchema)
async def get_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get a specific assessment"""
    require_permission("assessments:view")(current_user)
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.school_id == school_id
    ).first()
    
    if not assessment:
        raise NotFoundException("Assessment not found")
    
    return assessment

@router.put("/assessments/{assessment_id}", response_model=AssessmentSchema)
async def update_assessment(
    assessment_id: int,
    assessment_update: AssessmentUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update an assessment"""
    require_permission("assessments:update")(current_user)
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.school_id == school_id
    ).first()
    
    if not assessment:
        raise NotFoundException("Assessment not found")
    
    # Update fields
    for field, value in assessment_update.dict(exclude_unset=True).items():
        setattr(assessment, field, value)
    
    db.commit()
    db.refresh(assessment)
    
    return assessment

# Score endpoints
@router.post("/scores", response_model=ScoreSchema)
async def create_score(
    score: ScoreCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create a student score"""
    require_permission("scores:create")(current_user)
    
    # Verify assessment and student exist
    assessment = db.query(Assessment).filter(
        Assessment.id == score.assessment_id,
        Assessment.school_id == school_id
    ).first()
    if not assessment:
        raise NotFoundException("Assessment not found")
    
    student = db.query(Student).filter(
        Student.id == score.student_id,
        Student.school_id == school_id
    ).first()
    if not student:
        raise NotFoundException("Student not found")
    
    # Check if score already exists
    existing_score = db.query(Score).filter(
        Score.assessment_id == score.assessment_id,
        Score.student_id == score.student_id
    ).first()
    
    if existing_score:
        raise ValidationException("Score already exists for this student and assessment")
    
    # Validate score is within range
    if score.score < 0 or score.score > assessment.max_score:
        raise ValidationException(f"Score must be between 0 and {assessment.max_score}")
    
    db_score = Score(
        assessment_id=score.assessment_id,
        student_id=score.student_id,
        score=score.score,
        remarks=score.remarks,
        recorded_by=current_user.id,
        recorded_at=datetime.utcnow(),
        school_id=school_id
    )
    
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    
    return db_score

@router.get("/scores", response_model=List[ScoreSchema])
async def get_scores(
    skip: int = 0,
    limit: int = 100,
    assessment_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get student scores"""
    require_permission("scores:view")(current_user)
    
    query = db.query(Score).filter(Score.school_id == school_id)
    
    if assessment_id:
        query = query.filter(Score.assessment_id == assessment_id)
    if student_id:
        query = query.filter(Score.student_id == student_id)
    
    scores = query.offset(skip).limit(limit).all()
    return scores

@router.post("/scores/batch", response_model=List[ScoreSchema])
async def create_batch_scores(
    batch_scores: BatchScoreCreate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Create batch scores"""
    require_permission("scores:create")(current_user)
    
    # Verify assessment exists
    assessment = db.query(Assessment).filter(
        Assessment.id == batch_scores.assessment_id,
        Assessment.school_id == school_id
    ).first()
    if not assessment:
        raise NotFoundException("Assessment not found")
    
    created_scores = []
    
    for score_data in batch_scores.scores:
        # Check if score already exists
        existing = db.query(Score).filter(
            Score.assessment_id == batch_scores.assessment_id,
            Score.student_id == score_data["student_id"]
        ).first()
        
        if not existing:
            # Validate score
            if score_data["score"] < 0 or score_data["score"] > assessment.max_score:
                continue  # Skip invalid scores
            
            db_score = Score(
                assessment_id=batch_scores.assessment_id,
                student_id=score_data["student_id"],
                score=score_data["score"],
                remarks=score_data.get("remarks"),
                recorded_by=current_user.id,
                recorded_at=datetime.utcnow(),
                school_id=school_id
            )
            
            db.add(db_score)
            created_scores.append(db_score)
    
    db.commit()
    
    for score in created_scores:
        db.refresh(score)
    
    return created_scores

@router.put("/scores/{score_id}", response_model=ScoreSchema)
async def update_score(
    score_id: int,
    score_update: ScoreUpdate,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Update a student score"""
    require_permission("scores:update")(current_user)
    
    score = db.query(Score).filter(
        Score.id == score_id,
        Score.school_id == school_id
    ).first()
    
    if not score:
        raise NotFoundException("Score not found")
    
    # Validate score if being updated
    if score_update.score is not None:
        assessment = db.query(Assessment).filter(Assessment.id == score.assessment_id).first()
        if score_update.score < 0 or score_update.score > assessment.max_score:
            raise ValidationException(f"Score must be between 0 and {assessment.max_score}")
    
    # Update fields
    for field, value in score_update.dict(exclude_unset=True).items():
        setattr(score, field, value)
    
    db.commit()
    db.refresh(score)
    
    return score

@router.post("/assessments/{assessment_id}/publish")
async def publish_assessment_results(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Publish assessment results"""
    require_permission("assessments:publish")(current_user)
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.school_id == school_id
    ).first()
    
    if not assessment:
        raise NotFoundException("Assessment not found")
    
    assessment.is_published = True
    db.commit()
    
    return {"message": "Assessment results published successfully"}

@router.post("/assessments/{assessment_id}/withhold")
async def withhold_assessment_results(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Withhold assessment results"""
    require_permission("assessments:publish")(current_user)
    
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.school_id == school_id
    ).first()
    
    if not assessment:
        raise NotFoundException("Assessment not found")
    
    assessment.is_published = False
    db.commit()
    
    return {"message": "Assessment results withheld successfully"}

@router.get("/student/{student_id}/results")
async def get_student_results(
    student_id: int,
    term_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get all student results"""
    # Students can view their own results, parents their children's, teachers/admins all
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    # Check access permissions
    if current_user.id != student.user_id:
        # Check if parent
        from models.student import StudentParent
        parent_link = db.query(StudentParent).filter(
            StudentParent.student_id == student_id,
            StudentParent.parent_user_id == current_user.id
        ).first()
        
        if not parent_link:
            require_permission("scores:view")(current_user)
    
    query = db.query(Score).join(Assessment).filter(
        Score.student_id == student_id,
        Assessment.is_published == True
    )
    
    if term_id:
        query = query.filter(Assessment.term_id == term_id)
    
    scores = query.all()
    
    # Group by assessment and calculate totals
    results = []
    for score in scores:
        results.append({
            "assessment_id": score.assessment_id,
            "assessment_name": score.assessment.name,
            "subject": score.assessment.subject.name,
            "score": score.score,
            "max_score": score.assessment.max_score,
            "percentage": (score.score / score.assessment.max_score) * 100,
            "remarks": score.remarks,
            "date_conducted": score.assessment.date_conducted
        })
    
    return {"student_id": student_id, "results": results}

@router.get("/reports/student/{student_id}/term/{term_id}")
async def get_student_report_card(
    student_id: int,
    term_id: int,
    current_user: User = Depends(get_current_user),
    school_id: int = Depends(get_current_school),
    db: Session = Depends(get_db)
):
    """Get student report card for a term"""
    # Check permissions similar to above
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.school_id == school_id
    ).first()
    
    if not student:
        raise NotFoundException("Student not found")
    
    # Check access permissions
    if current_user.id != student.user_id:
        from models.student import StudentParent
        parent_link = db.query(StudentParent).filter(
            StudentParent.student_id == student_id,
            StudentParent.parent_user_id == current_user.id
        ).first()
        
        if not parent_link:
            require_permission("reports:view")(current_user)
    
    # Get all assessments and scores for the term
    scores = db.query(Score).join(Assessment).filter(
        Score.student_id == student_id,
        Assessment.term_id == term_id,
        Assessment.is_published == True
    ).all()
    
    # Group by subject and calculate subject totals
    subject_scores = {}
    for score in scores:
        subject_id = score.assessment.subject_id
        subject_name = score.assessment.subject.name
        
        if subject_id not in subject_scores:
            subject_scores[subject_id] = {
                "subject_name": subject_name,
                "assessments": [],
                "total_score": 0,
                "total_max": 0
            }
        
        subject_scores[subject_id]["assessments"].append({
            "name": score.assessment.name,
            "score": score.score,
            "max_score": score.assessment.max_score,
            "component": score.assessment.component.name
        })
        
        subject_scores[subject_id]["total_score"] += score.score
        subject_scores[subject_id]["total_max"] += score.assessment.max_score
    
    # Calculate grades
    grading_scale = db.query(GradingScale).filter(
        GradingScale.school_id == school_id
    ).order_by(GradingScale.min_score.desc()).all()
    
    def get_grade(percentage):
        for grade in grading_scale:
            if percentage >= grade.min_score:
                return grade.grade
        return "F"
    
    report_card = {
        "student_id": student_id,
        "student_name": f"{student.user.first_name} {student.user.last_name}",
        "term_id": term_id,
        "subjects": []
    }
    
    for subject_data in subject_scores.values():
        percentage = (subject_data["total_score"] / subject_data["total_max"]) * 100 if subject_data["total_max"] > 0 else 0
        grade = get_grade(percentage)
        
        report_card["subjects"].append({
            "subject_name": subject_data["subject_name"],
            "total_score": subject_data["total_score"],
            "total_max": subject_data["total_max"],
            "percentage": percentage,
            "grade": grade,
            "assessments": subject_data["assessments"]
        })
    
    return report_card
