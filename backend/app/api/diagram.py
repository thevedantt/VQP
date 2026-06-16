"""Diagram detection and generation endpoints."""

import base64
import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_diagram_retrieval_service,
    get_diagram_router,
    get_diagram_service,
    get_diagram_template_service,
    get_physics_understanding_service,
    get_schema_adaptation_service,
    get_schema_population_service,
)
from app.models.requests import DetectDiagramRequest, DiagramRetrieveAndGenerateRequest, GenerateDiagramRequest
from app.models.responses import DetectDiagramResponse, DiagramRetrieveAndGenerateResponse, GenerateDiagramResponse
from app.services.diagram_retrieval_service import DiagramRetrievalService
from app.services.diagram_router import DiagramRouter
from app.services.diagram_service import DiagramService
from app.services.diagram_template_service import DiagramTemplateService
from app.services.physics_understanding_service import PhysicsUnderstandingService
from app.services.schema_adaptation_service import SchemaAdaptationService
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
    diagram_router: DiagramRouter = Depends(get_diagram_router),
) -> GenerateDiagramResponse:
    """Generate a diagram specification and ready-to-render SVG for the given type and question using the Target Architecture."""

    analysis = physics_understanding.analyze(request.question)
    diagram_type = request.diagram_type if request.diagram_type != "none" else analysis.diagram_type

    template_id, template = template_service.select(diagram_type, analysis.concept, analysis.scenario)
    semantic_schema = schema_service.build_semantic_schema(analysis, template_id, template)

    if semantic_schema["diagram_type"] != diagram_type:
        semantic_schema["diagram_type"] = diagram_type

    result = diagram_router.generate(semantic_schema, request.question, template)

    return GenerateDiagramResponse(
        diagram_type=diagram_type,
        diagram_specification=result.render_schema,
        svg=result.svg,
    )


@router.post("/diagram/retrieve-and-generate", response_model=DiagramRetrieveAndGenerateResponse)
def retrieve_and_generate_diagram(
    request: DiagramRetrieveAndGenerateRequest,
    retrieval_service: DiagramRetrievalService = Depends(get_diagram_retrieval_service),
    adaptation_service: SchemaAdaptationService = Depends(get_schema_adaptation_service),
    diagram_router: DiagramRouter = Depends(get_diagram_router),
) -> DiagramRetrieveAndGenerateResponse:
    """Retrieve the most similar diagram schema from the library and generate a new diagram."""

    classification = retrieval_service.classify(request.question)
    renderer_type = classification["renderer_type"]

    retrieved_schema, similarity_score, _ = retrieval_service.retrieve_similarity_details(
        request.question, renderer_type
    )

    adapted_schema = adaptation_service.adapt(request.question, retrieved_schema or {}, classification)

    diagram_type = _renderer_to_diagram_type(renderer_type)
    generator_input = {
        "entities": adapted_schema.get("required_entities", []),
        "scenario": adapted_schema.get("scenario", "default"),
        "rules": adapted_schema.get("rules", {}),
        "concept": adapted_schema.get("concept", ""),
        "extra": adapted_schema.get("extra", {}),
    }
    result = diagram_router._legacy(diagram_type, generator_input, request.question)

    svg_data = base64.b64encode(result.svg.encode("utf-8")).decode("utf-8")
    diagram_url = f"data:image/svg+xml;base64,{svg_data}"

    return DiagramRetrieveAndGenerateResponse(
        question=request.question,
        classification=classification,
        retrieved_schema_id=retrieved_schema.get("question_id", "") if retrieved_schema else "",
        similarity_score=similarity_score,
        diagram_schema=result.render_schema,
        diagram_url=diagram_url,
    )


def _renderer_to_diagram_type(renderer_type: str) -> str:
    mapping = {
        "ray_optics": "ray_diagram",
        "circuit": "circuit",
        "magnetic_field": "magnetic_field",
        "graph": "graph",
        "free_body": "free_body",
    }
    return mapping.get(renderer_type, "none")
