"""Debug endpoint exposing every stage of the Dynamic Physics Semantic Schema
pipeline:

    Question -> Understanding Layer -> Semantic Schema -> Template Selection
             -> Render Schema -> Final Diagram

Additive only - does not affect ``/api/generate-paper`` or ``/api/generate-diagram``.
"""

import logging
from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_diagram_template_service,
    get_physics_understanding_service,
    get_schema_population_service,
)
from app.models.requests import AnalyzeDiagramRequest
from app.models.responses import AnalyzeDiagramResponse, PhysicsAnalysisModel
from app.services.diagram_svg import render_svg
from app.services.diagram_template_service import DiagramTemplateService
from app.services.physics_understanding_service import PhysicsUnderstandingService
from app.services.schema_population_service import SchemaPopulationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.post("/analyze-diagram", response_model=AnalyzeDiagramResponse)
def analyze_diagram(
    request: AnalyzeDiagramRequest,
    physics_understanding: PhysicsUnderstandingService = Depends(get_physics_understanding_service),
    template_service: DiagramTemplateService = Depends(get_diagram_template_service),
    schema_service: SchemaPopulationService = Depends(get_schema_population_service),
) -> AnalyzeDiagramResponse:
    """Run the full physics-analysis -> template -> schema -> SVG pipeline and
    return every intermediate artifact for inspection."""

    analysis = physics_understanding.analyze(request.question)
    template_id, template = template_service.select(analysis.diagram_type, analysis.concept, analysis.scenario)
    semantic_schema = schema_service.build_semantic_schema(analysis, template_id, template)
    render_schema = schema_service.build_render_schema(semantic_schema, request.question, template)
    svg = render_svg(render_schema)

    analysis_dict = asdict(analysis)
    return AnalyzeDiagramResponse(
        question=request.question,
        physics_analysis=PhysicsAnalysisModel(**analysis_dict),
        understanding=analysis_dict["understanding"],
        selected_template=template,
        semantic_schema=semantic_schema,
        render_schema=render_schema,
        svg=svg,
    )
