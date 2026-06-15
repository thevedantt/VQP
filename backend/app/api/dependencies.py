"""Dependency-injection providers for FastAPI routes.

Each provider is wrapped in ``lru_cache`` so it is constructed once (lazily,
on first use) and reused as a singleton for the lifetime of the process -
the JSON datasets and Gemini client are loaded/configured a single time.
"""

from functools import lru_cache

from app.core.config import get_settings
from app.services.book_service import BookService
from app.services.diagram_service import DiagramService
from app.services.diagram_taxonomy_service import DiagramTaxonomyService
from app.services.diagram_template_service import DiagramTemplateService
from app.services.gemini_service import GeminiService
from app.services.openrouter_service import OpenRouterService
from app.services.orchestrator_service import PaperGenerationOrchestrator
from app.services.paper_evaluator import PaperEvaluator
from app.services.paper_service import PaperService
from app.services.physics_understanding_service import PhysicsUnderstandingService
from app.services.schema_population_service import SchemaPopulationService
from app.services.question_service import QuestionService
from app.services.weightage_service import WeightageService


@lru_cache
def get_question_service() -> QuestionService:
    settings = get_settings()
    return QuestionService(settings.labeled_questions_file)


@lru_cache
def get_book_service() -> BookService:
    settings = get_settings()
    return BookService(settings.book_chapters_dir)


@lru_cache
def get_diagram_service() -> DiagramService:
    settings = get_settings()
    return DiagramService(settings.diagram_dataset_file)


@lru_cache
def get_gemini_service() -> GeminiService:
    settings = get_settings()
    return GeminiService(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model,
        max_retries=settings.gemini_max_retries,
        retry_backoff_seconds=settings.gemini_retry_backoff_seconds,
        request_timeout_seconds=settings.gemini_request_timeout_seconds,
    )


@lru_cache
def get_openrouter_service() -> OpenRouterService:
    settings = get_settings()
    return OpenRouterService(
        api_key=settings.openrouter_api_key,
        model_name=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
        max_retries=settings.openrouter_max_retries,
        retry_backoff_seconds=settings.openrouter_retry_backoff_seconds,
        request_timeout_seconds=settings.openrouter_request_timeout_seconds,
    )


@lru_cache
@lru_cache
def get_diagram_taxonomy_service() -> DiagramTaxonomyService:
    settings = get_settings()
    return DiagramTaxonomyService(settings.diagram_taxonomy_dir)


@lru_cache
def get_diagram_template_service() -> DiagramTemplateService:
    settings = get_settings()
    return DiagramTemplateService(settings.diagram_templates_dir)


@lru_cache
def get_physics_understanding_service() -> PhysicsUnderstandingService:
    return PhysicsUnderstandingService(
        get_openrouter_service(),
        get_gemini_service(),
        get_diagram_service(),
        get_diagram_taxonomy_service(),
        get_diagram_template_service(),
    )


@lru_cache
def get_schema_population_service() -> SchemaPopulationService:
    return SchemaPopulationService()


@lru_cache
def get_paper_evaluator() -> PaperEvaluator:
    return PaperEvaluator()


@lru_cache
def get_weightage_service() -> WeightageService:
    return WeightageService(get_question_service(), get_book_service())


@lru_cache
def get_paper_service() -> PaperService:
    return PaperService(
        get_question_service(),
        get_book_service(),
        get_gemini_service(),
        get_openrouter_service(),
        get_diagram_service(),
    )


@lru_cache
def get_orchestrator() -> PaperGenerationOrchestrator:
    return PaperGenerationOrchestrator(
        get_weightage_service(),
        get_paper_service(),
        get_diagram_service(),
        get_physics_understanding_service(),
        get_diagram_template_service(),
        get_schema_population_service(),
        get_paper_evaluator(),
    )
