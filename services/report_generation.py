from sqlalchemy.orm import Session, joinedload
from models.school import ReportTemplate, School
from models.student import Student
from models.user import User
from models.academic import SubjectResult, TermResult, StudentCumulativeResult, Term, AcademicSession, Subject
from typing import Dict, Any, Optional
from jinja2 import Template
from weasyprint import HTML
from utils.exceptions import NotFoundException

class ReportGenerationService:
    def __init__(self, db: Session):
        self.db = db

    def _get_student_data(self, student_id: int, school_id: int) -> Dict[str, Any]:
        student = self.db.query(Student).filter(
            Student.id == student_id,
            Student.school_id == school_id
        ).options(joinedload(Student.user)).first()

        if not student:
            raise NotFoundException("Student not found")

        return {
            "student_id": student.student_id,
            "first_name": student.user.first_name,
            "last_name": student.user.last_name,
            "full_name": f"{student.user.first_name} {student.user.last_name}",
            "admission_number": student.admission_number,
            "class_name": student.class_assigned.name if student.class_assigned else "N/A",
            "admission_date": str(student.admission_date),
            "date_of_birth": str(student.user.date_of_birth),
            "gender": student.user.gender,
            "contact_email": student.user.email,
            "contact_phone": student.user.phone,
            "address": student.user.address,
            "school_id": student.school_id
        }

    def _get_school_data(self, school_id: int) -> Dict[str, Any]:
        school = self.db.query(School).filter(School.id == school_id).first()
        if not school:
            raise NotFoundException("School not found")
        return {
            "school_name": school.name,
            "school_address": school.address,
            "school_phone": school.phone,
            "school_email": school.email,
            "school_website": school.website,
            "school_logo_url": school.logo_url,
            "principal_name": school.principal_name
        }

    def _get_term_results_data(self, student_id: int, term_id: int, school_id: int) -> Dict[str, Any]:
        term = self.db.query(Term).filter(Term.id == term_id, Term.school_id == school_id).first()
        if not term:
            raise NotFoundException("Term not found")

        subject_results = self.db.query(SubjectResult).filter(
            SubjectResult.student_id == student_id,
            SubjectResult.term_id == term_id,
            SubjectResult.school_id == school_id
        ).options(joinedload(SubjectResult.subject)).all()

        term_result = self.db.query(TermResult).filter(
            TermResult.student_id == student_id,
            TermResult.term_id == term_id,
            TermResult.school_id == school_id
        ).first()

        subjects_data = []
        for sr in subject_results:
            subjects_data.append({
                "subject_name": sr.subject.name,
                "total_score": sr.total_score,
                "grade": sr.grade,
                "gpa": sr.gpa,
                "rank": sr.rank,
                "remarks": sr.remarks
            })
        
        return {
            "term_name": term.name,
            "academic_session_name": term.academic_session.name if term.academic_session else "N/A",
            "subjects": subjects_data,
            "overall_gpa": term_result.total_gpa if term_result else None,
            "overall_grade": term_result.overall_grade if term_result else None,
            "position_in_class": term_result.position_in_class if term_result else None,
            "term_remarks": term_result.remarks if term_result else None
        }

    def generate_report_pdf(
        self,
        template_id: int,
        student_id: int,
        term_id: Optional[int] = None,
        academic_session_id: Optional[int] = None,
        school_id: int = None
    ) -> bytes:
        template_obj = self.db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
        if not template_obj:
            raise NotFoundException("Report template not found")

        # Gather data for the template
        data = {
            "school": self._get_school_data(school_id),
            "student": self._get_student_data(student_id, school_id),
            "term_results": None,
            "academic_session_results": None
        }

        if term_id:
            data["term_results"] = self._get_term_results_data(student_id, term_id, school_id)
        # Add logic for academic_session_id if needed for cumulative reports

        # Render the HTML template with data
        template = Template(template_obj.html_content)
        rendered_html = template.render(data)

        # Convert HTML to PDF
        pdf = HTML(string=rendered_html).write_pdf()
        return pdf
