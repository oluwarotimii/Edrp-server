from sqlalchemy.orm import Session
from models.academic import SubjectResult, Term, Subject, Class, AcademicSession, TermResult, StudentCumulativeResult
from models.student import Student
from models.assessment import GradingScale
from typing import List, Dict, Any, Optional
from collections import defaultdict
from utils.exceptions import NotFoundException, ValidationException

def calculate_subject_result_and_gpa(
    db: Session,
    student_id: int,
    subject_id: int,
    term_id: int,
    total_score: float,
    school_id: int
) -> SubjectResult:
    """Calculates grade and GPA for a subject result and creates/updates SubjectResult."""
    
    # Fetch grading scale for the school
    grading_scale = db.query(GradingScale).filter(
        GradingScale.school_id == school_id
    ).order_by(GradingScale.min_score.desc()).all()

    if not grading_scale:
        raise ValidationException("No grading scale defined for this school.")

    grade = "F"
    gpa_value = None

    for g_scale in grading_scale:
        if total_score >= g_scale.min_score:
            grade = g_scale.grade
            gpa_value = g_scale.gpa_value
            break

    subject_result = db.query(SubjectResult).filter(
        SubjectResult.student_id == student_id,
        SubjectResult.subject_id == subject_id,
        SubjectResult.term_id == term_id
    ).first()

    if not subject_result:
        subject_result = SubjectResult(
            student_id=student_id,
            subject_id=subject_id,
            term_id=term_id,
            school_id=school_id
        )
    
    subject_result.total_score = total_score
    subject_result.grade = grade
    subject_result.gpa = gpa_value

    db.add(subject_result)
    db.commit()
    db.refresh(subject_result)
    return subject_result


def calculate_class_ranks(
    db: Session,
    term_id: int,
    class_id: int,
    school_id: int
):
    """Calculates and updates ranks for students within a specific class for a term."""
    subject_results = db.query(SubjectResult).join(Student).filter(
        SubjectResult.term_id == term_id,
        Student.class_id == class_id,
        SubjectResult.school_id == school_id
    ).order_by(SubjectResult.total_score.desc()).all()

    if not subject_results:
        return

    # Group by student to get total scores for ranking
    student_total_scores = defaultdict(float)
    for sr in subject_results:
        student_total_scores[sr.student_id] += sr.total_score

    # Sort students by their total scores
    sorted_students = sorted(student_total_scores.items(), key=lambda item: item[1], reverse=True)

    # Assign ranks (handling ties)
    current_rank = 0
    last_score = -1
    for i, (student_id, score) in enumerate(sorted_students):
        if score != last_score:
            current_rank = i + 1
        
        # Update rank for all subject results of this student in this term
        db.query(SubjectResult).filter(
            SubjectResult.student_id == student_id,
            SubjectResult.term_id == term_id
        ).update({"rank": current_rank}, synchronize_session=False)
        
        last_score = score
    
    db.commit()


def calculate_term_gpa_and_overall_results(
    db: Session,
    term_id: int,
    student_id: int,
    school_id: int
):
    """Calculates and updates Term GPA and overall results for a student for a term."""
    subject_results = db.query(SubjectResult).filter(
        SubjectResult.student_id == student_id,
        SubjectResult.term_id == term_id,
        SubjectResult.school_id == school_id
    ).all()

    if not subject_results:
        return

    total_gpa_points = 0.0
    total_credit_units = 0
    total_score_sum = 0.0

    for sr in subject_results:
        subject = db.query(Subject).filter(Subject.id == sr.subject_id).first()
        if subject and sr.gpa is not None:
            total_gpa_points += (sr.gpa * subject.credit_units)
            total_credit_units += subject.credit_units
        total_score_sum += sr.total_score

    term_gpa = total_gpa_points / total_credit_units if total_credit_units > 0 else None
    overall_percentage = (total_score_sum / (len(subject_results) * 100)) * 100 if subject_results else 0 # Assuming max 100 per subject

    # Determine overall grade for the term
    grading_scale = db.query(GradingScale).filter(
        GradingScale.school_id == school_id
    ).order_by(GradingScale.min_score.desc()).all()

    overall_grade = "F"
    for g_scale in grading_scale:
        if overall_percentage >= g_scale.min_score:
            overall_grade = g_scale.grade
            break

    term_result = db.query(TermResult).filter(
        TermResult.student_id == student_id,
        TermResult.term_id == term_id
    ).first()

    if not term_result:
        term_result = TermResult(
            student_id=student_id,
            term_id=term_id,
            school_id=school_id
        )
    
    term_result.total_gpa = term_gpa
    term_result.total_score = total_score_sum
    term_result.overall_grade = overall_grade
    # position_in_class will be calculated separately if needed
    
    db.add(term_result)
    db.commit()
    db.refresh(term_result)
    return term_result


def calculate_cumulative_gpa_and_overall_results(
    db: Session,
    student_id: int,
    academic_session_id: int,
    school_id: int
):
    """Calculates and updates Cumulative GPA and overall results for a student for an academic session."""
    term_results = db.query(TermResult).join(Term).filter(
        TermResult.student_id == student_id,
        Term.academic_session_id == academic_session_id,
        TermResult.school_id == school_id
    ).all()

    if not term_results:
        return

    total_gpa_points = 0.0
    total_credit_units = 0
    total_score_sum = 0.0

    for tr in term_results:
        # Assuming each term contributes equally or based on some weighting
        # For simplicity, let's sum up subject results from all terms in the session
        subject_results_in_term = db.query(SubjectResult).filter(
            SubjectResult.student_id == student_id,
            SubjectResult.term_id == tr.term_id,
            SubjectResult.school_id == school_id
        ).all()

        for sr in subject_results_in_term:
            subject = db.query(Subject).filter(Subject.id == sr.subject_id).first()
            if subject and sr.gpa is not None:
                total_gpa_points += (sr.gpa * subject.credit_units)
                total_credit_units += subject.credit_units
            total_score_sum += sr.total_score

    cumulative_gpa = total_gpa_points / total_credit_units if total_credit_units > 0 else None
    overall_percentage = (total_score_sum / (len(term_results) * 100 * len(subject_results_in_term))) * 100 if term_results and subject_results_in_term else 0 # Rough estimate

    # Determine overall cumulative grade
    grading_scale = db.query(GradingScale).filter(
        GradingScale.school_id == school_id
    ).order_by(GradingScale.min_score.desc()).all()

    overall_cumulative_grade = "F"
    for g_scale in grading_scale:
        if overall_percentage >= g_scale.min_score:
            overall_cumulative_grade = g_scale.grade
            break

    cumulative_result = db.query(StudentCumulativeResult).filter(
        StudentCumulativeResult.student_id == student_id,
        StudentCumulativeResult.academic_session_id == academic_session_id
    ).first()

    if not cumulative_result:
        cumulative_result = StudentCumulativeResult(
            student_id=student_id,
            academic_session_id=academic_session_id,
            school_id=school_id
        )
    
    cumulative_result.cumulative_gpa = cumulative_gpa
    cumulative_result.cumulative_score = total_score_sum
    cumulative_result.overall_cumulative_grade = overall_cumulative_grade
    # overall_cumulative_position will be calculated separately if needed

    db.add(cumulative_result)
    db.commit()
    db.refresh(cumulative_result)
    return cumulative_result


def calculate_overall_class_positions(
    db: Session,
    term_id: int,
    class_id: int,
    school_id: int
):
    """Calculates and updates overall positions for students within a specific class for a term based on total scores."""
    term_results = db.query(TermResult).join(Student).filter(
        TermResult.term_id == term_id,
        Student.class_id == class_id,
        TermResult.school_id == school_id
    ).order_by(TermResult.total_score.desc()).all()

    if not term_results:
        return

    current_position = 0
    last_score = -1
    for i, tr in enumerate(term_results):
        if tr.total_score != last_score:
            current_position = i + 1
        
        tr.position_in_class = current_position
        db.add(tr)
        last_score = tr.total_score
    
    db.commit()


def calculate_overall_academic_session_positions(
    db: Session,
    academic_session_id: int,
    school_id: int
):
    """Calculates and updates overall positions for students within an academic session based on cumulative scores."""
    cumulative_results = db.query(StudentCumulativeResult).filter(
        StudentCumulativeResult.academic_session_id == academic_session_id,
        StudentCumulativeResult.school_id == school_id
    ).order_by(StudentCumulativeResult.cumulative_score.desc()).all()

    if not cumulative_results:
        return

    current_position = 0
    last_score = -1
    for i, cr in enumerate(cumulative_results):
        if cr.cumulative_score != last_score:
            current_position = i + 1
        
        cr.overall_cumulative_position = current_position
        db.add(cr)
        last_score = cr.cumulative_score
    
    db.commit()
