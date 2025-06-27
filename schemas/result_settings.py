from pydantic import BaseModel
from typing import Optional

class ResultSettings(BaseModel):
    auto_calculate_results: bool = True
    auto_publish_results: bool = False
    include_teacher_comments: bool = True
    include_principal_comments: bool = True
    grading_scale_id: Optional[int] = None
    default_assessment_scheme_id: Optional[int] = None
    selected_grading_profile_id: Optional[int] = None
    custom_assessment_scheme_id: Optional[int] = None
    custom_grading_scale_id: Optional[int] = None
