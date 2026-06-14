"""Diagram detection and generation endpoints."""

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_diagram_service
from app.models.requests import DetectDiagramRequest, GenerateDiagramRequest
from app.models.responses import DetectDiagramResponse, GenerateDiagramResponse
from app.services.diagram_service import DiagramService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["diagram"])


@router.post("/detect-diagram", response_model=DetectDiagramResponse)
def detect_diagram(
    request: DetectDiagramRequest,
    diagram_service: DiagramService = Depends(get_diagram_service),
) -> DetectDiagramResponse:
    """Determine whether a question requires a diagram, and which type."""

    result = diagram_service.detect(request.question)
    return DetectDiagramResponse(
        requires_diagram=result.requires_diagram,
        diagram_type=result.diagram_type,
        confidence=result.confidence,
        reason=result.reason,
    )


@router.post("/generate-diagram", response_model=GenerateDiagramResponse)
def generate_diagram(
    request: GenerateDiagramRequest,
    diagram_service: DiagramService = Depends(get_diagram_service),
) -> GenerateDiagramResponse:
    """Generate a diagram specification and ready-to-render SVG for the given type and question."""

    diagram = diagram_service.build_diagram(request.diagram_type, request.question)
    return GenerateDiagramResponse(
        diagram_type=diagram["diagram_type"],
        diagram_specification=diagram["specification"],
        svg=diagram["svg"],
    )
