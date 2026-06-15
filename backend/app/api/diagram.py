"""Diagram detection and generation endpoints."""

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_diagram_service,
    get_diagram_template_service,
    get_physics_understanding_service,
    get_schema_population_service,
)
from app.models.requests import DetectDiagramRequest, GenerateDiagramRequest
from app.models.responses import DetectDiagramResponse, GenerateDiagramResponse
from app.services.diagram_service import DiagramService
from app.services.diagram_svg import render_svg
from app.services.diagram_template_service import DiagramTemplateService
from app.services.physics_understanding_service import PhysicsUnderstandingService
from app.services.schema_population_service import SchemaPopulationService

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
    physics_understanding: PhysicsUnderstandingService = Depends(get_physics_understanding_service),
    template_service: DiagramTemplateService = Depends(get_diagram_template_service),
    schema_service: SchemaPopulationService = Depends(get_schema_population_service),
) -> GenerateDiagramResponse:
    """Generate a diagram specification and ready-to-render SVG for the given type and question using the Target Architecture."""

    analysis = physics_understanding.analyze(request.question)
    diagram_type = request.diagram_type if request.diagram_type != "none" else analysis.diagram_type

    template_id, template = template_service.select(diagram_type, analysis.concept, analysis.scenario)
    semantic_schema = schema_service.build_semantic_schema(analysis, template_id, template)

    if semantic_schema["diagram_type"] != diagram_type:
        semantic_schema["diagram_type"] = diagram_type

    render_schema = schema_service.build_render_schema(semantic_schema, request.question, template)
    svg = render_svg(render_schema)

    return GenerateDiagramResponse(
        diagram_type=diagram_type,
        diagram_specification=render_schema,
        svg=svg,
    )
