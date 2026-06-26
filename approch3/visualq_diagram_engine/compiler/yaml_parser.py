"""YAML file loader and spec parser."""

import logging
from pathlib import Path
from typing import Any

import yaml

from visualq_diagram_engine.primitives.styles import Style

logger = logging.getLogger(__name__)


class ParseError(Exception):
    pass


class YAMLParser:
    def load(self, path: str) -> dict:
        """Load and parse a YAML file. Raises ParseError on failure."""
        p = Path(path)
        if not p.exists():
            raise ParseError(f"Template file not found: {path}")
        try:
            with p.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ParseError(f"Invalid YAML in {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ParseError(f"Expected a YAML mapping at the top level, got {type(data)}")
        logger.debug("Loaded YAML: %s (%d top-level keys)", path, len(data))
        return data

    def parse_style(self, d: dict) -> Style:
        """Convert a style dict to a Style model."""
        if not d:
            return Style()
        # Map YAML snake_case keys directly — Pydantic v2 handles extras gracefully
        return Style(**{k: v for k, v in d.items() if k in Style.model_fields})

    def parse_position(self, d: dict) -> tuple[float, float]:
        """Extract (x, y) position from an object spec dict."""
        return (float(d.get("x", 0)), float(d.get("y", 0)))
