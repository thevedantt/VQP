"""VisualQ Pilot FastAPI application entrypoint.

Run locally with:

    uvicorn app.main:app --reload --app-dir backend
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import debug, diagram, health, paper
from app.api.dependencies import get_orchestrator
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered CBSE Physics assessment platform: generates unit tests "
    "mixing PYQs and NCERT-grounded AI questions, with automatic diagram detection.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(paper.router)
app.include_router(diagram.router)
app.include_router(debug.router)


@app.on_event("startup")
async def on_startup() -> None:
    """Eagerly load all datasets and build the service graph so failures surface at boot."""

    logger.info("Starting %s v%s (env=%s)", settings.app_name, settings.app_version, settings.environment)
    get_orchestrator()
    logger.info("All datasets loaded and services initialized successfully.")
