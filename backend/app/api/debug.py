"""Debug endpoint exposing every stage of the Dynamic Physics Semantic Schema
pipeline:

    Question -> Physics Understanding -> NCERT Context -> Semantic Schema
             -> Generator Selected -> Generator Input -> Validation Report
             -> Final Diagram

Additive only - does not affect ``/api/generate-paper`` or ``/api/generate-diagram``.
"""

import logging
from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_diagram_router,
    get_diagram_template_service,
    get_diagram_validation_service,
    get_physics_understanding_service,
    get_schema_population_service,
)
from app.models.requests import AnalyzeDiagramRequest
from app.models.responses import (
    AnalyzeDiagramResponse,
    GeneratorSelectionModel,
    NcertContextModel,
    PhysicsAnalysisModel,
    ValidationReportModel,
)
from app.services.diagram_router import DiagramRouter
from app.services.diagram_template_service import DiagramTemplateService
from app.services.diagram_validation_service import DiagramValidationService
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
    diagram_router: DiagramRouter = Depends(get_diagram_router),
    validation_service: DiagramValidationService = Depends(get_diagram_validation_service),
) -> AnalyzeDiagramResponse:
    """Run the full physics-analysis -> NCERT -> schema -> router -> validation
    pipeline and return every intermediate artifact for inspection."""

    analysis = physics_understanding.analyze(request.question)
    template_id, template = template_service.select(analysis.diagram_type, analysis.concept, analysis.scenario)
    semantic_schema = schema_service.build_semantic_schema(analysis, template_id, template)

    result = diagram_router.generate(semantic_schema, request.question, template)
    validation_report = validation_service.validate(semantic_schema, result.render_schema, result.svg)

    analysis_dict = asdict(analysis)
    return AnalyzeDiagramResponse(
        question=request.question,
        physics_analysis=PhysicsAnalysisModel(**analysis_dict),
        understanding=analysis_dict["understanding"],
        ncert_context=NcertContextModel(**analysis.textbook_context),
        selected_template=template,
        semantic_schema=semantic_schema,
        generator_selection=GeneratorSelectionModel(
            engine=result.engine,
            diagram_type=semantic_schema["diagram_type"],
            concept=semantic_schema["concept"],
            scenario=semantic_schema["scenario"],
        ),
        generator_input=result.generator_input,
        render_schema=result.render_schema,
        validation_report=ValidationReportModel(**validation_report),
        svg=result.svg,
    )
