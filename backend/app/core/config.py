"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> backend/app/data
APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = "VisualQ Pilot API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    gemini_max_retries: int = 3
    gemini_retry_backoff_seconds: float = 1.5
    gemini_request_timeout_seconds: float = 30.0

    # Data paths
    question_bank_dir: Path = DATA_DIR / "question_bank"
    book_dir: Path = DATA_DIR / "Book"

    labeled_questions_file: Path = DATA_DIR / "question_bank" / "labeled_questions.json"
    final_dataset_file: Path = DATA_DIR / "question_bank" / "final_dataset.json"
    diagram_dataset_file: Path = DATA_DIR / "question_bank" / "diagram_dataset.json"

    chapter_index_file: Path = DATA_DIR / "Book" / "chapter_index.json"
    book_knowledge_base_file: Path = DATA_DIR / "Book" / "physics_part1_knowledge_base.json"
    book_chapters_dir: Path = DATA_DIR / "Book" / "chapters"

    # Paper generation defaults
    default_total_questions: int = 16
    max_total_questions: int = 50
    book_excerpt_max_chars: int = 2500


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
