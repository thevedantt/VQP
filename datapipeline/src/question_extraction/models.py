from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class QuestionModel(BaseModel):
    question_no: int
    source_file: str
    section: str
    type: str
    marks: int
    chapter: Optional[str] = None
    question: str
    options: Dict[str, str] = Field(default_factory=dict)

class ExtractionReportModel(BaseModel):
    file: str
    questions_found: int
    mcqs: int
    vsa: int
    sa: int
    case_study: int
    la: int
    status: str
