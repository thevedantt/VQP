"""Paper generation endpoint."""

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_orchestrator
from app.models.requests import GeneratePaperRequest
from app.models.responses import GeneratedPaperResponse
from app.services.orchestrator_service import PaperGenerationOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["paper"])


@router.post("/generate-paper", response_model=GeneratedPaperResponse)
def generate_paper(
    request: GeneratePaperRequest,
    orchestrator: PaperGenerationOrchestrator = Depends(get_orchestrator),
) -> GeneratedPaperResponse:
    """Generate a CBSE Physics unit test mixing PYQ and AI-generated questions."""

    return orchestrator.generate_paper(request)
