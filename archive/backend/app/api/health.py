"""Health check endpoint."""

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_book_service, get_diagram_service, get_gemini_service, get_question_service
from app.core.config import Settings, get_settings
from app.models.responses import HealthResponse
from app.services.book_service import BookService
from app.services.diagram_service import DiagramService
from app.services.gemini_service import GeminiService
from app.services.question_service import QuestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    settings: Settings = Depends(get_settings),
    question_service: QuestionService = Depends(get_question_service),
    book_service: BookService = Depends(get_book_service),
    diagram_service: DiagramService = Depends(get_diagram_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
) -> HealthResponse:
    """Report service status and loaded dataset sizes."""

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        gemini_configured=gemini_service.is_configured,
        datasets={
            "pyq_questions": len(question_service.get_all()),
            "ncert_chapters": len(book_service.get_available_chapters()),
            "diagram_labels": diagram_service.labeled_count,
        },
    )
