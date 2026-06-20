"""Pydantic request models for the VisualQ Pilot API."""

from pydantic import BaseModel, Field, model_validator

from app.models.enums import DifficultyLevel, DiagramType, QuestionType


class GeneratePaperRequest(BaseModel):
    """Input payload for POST /api/generate-paper."""

    difficulty: DifficultyLevel = Field(
        default="medium", description="Overall difficulty level for the generated paper."
    )
    pyq_percentage: int = Field(
        default=60, ge=0, le=100, description="Percentage of questions sourced from previous year papers."
    )
    ai_percentage: int = Field(
        default=40, ge=0, le=100, description="Percentage of questions generated fresh via Gemini."
    )
    include_diagrams: bool = Field(
        default=True, description="Whether to run diagram detection and generate diagram specifications."
    )
    diagram_percentage: int = Field(
        default=40,
        ge=0,
        le=100,
        description="Target percentage of questions that should require a diagram (e.g. 40 for ~40%).",
    )
    total_questions: int = Field(
        default=16, ge=4, le=50, description="Total number of questions to include in the paper."
    )
    chapters: list[str] | None = Field(
        default=None,
        description="Optional subset of NCERT chapters to restrict the paper to. Defaults to all available chapters.",
    )

    @model_validator(mode="after")
    def _validate_percentages(self) -> "GeneratePaperRequest":
        if self.pyq_percentage + self.ai_percentage != 100:
            raise ValueError("pyq_percentage and ai_percentage must sum to 100")
        return self


class DetectDiagramRequest(BaseModel):
    """Input payload for POST /api/detect-diagram."""

    question: str = Field(..., min_length=3, max_length=5000, description="Question text to analyze.")


class GenerateDiagramRequest(BaseModel):
    """Input payload for POST /api/generate-diagram."""

    diagram_type: DiagramType = Field(..., description="Type of diagram to generate a specification for.")
    question: str = Field(..., min_length=3, max_length=5000, description="Question text used to ground the diagram.")


class DiagramRetrieveAndGenerateRequest(BaseModel):
    """Input payload for POST /api/diagram/retrieve-and-generate."""

    question: str = Field(..., min_length=3, max_length=5000, description="Physics question text for diagram retrieval and generation.")


class AnalyzeDiagramRequest(BaseModel):
    """Input payload for POST /api/debug/analyze-diagram."""

    question: str = Field(..., min_length=3, max_length=5000, description="Question text to analyze.")


class GenerateQuestionRequest(BaseModel):
    """Internal request shape used by the Gemini question generator."""

    chapter: str = Field(..., description="NCERT chapter name to ground the generated question in.")
    difficulty: DifficultyLevel = Field(default="medium")
    marks: int = Field(..., ge=1, le=5)
    question_type: QuestionType = Field(default="SA")
