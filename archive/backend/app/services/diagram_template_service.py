"""Loads the static diagram template library (concept + scenario -> categorical rules).

Templates under ``data/diagram_templates/`` describe, per
``{diagram_type}_{concept}``, the categorical (non-numeric) rules that
``SchemaPopulationService`` merges with a ``PhysicsAnalysis`` to build a
semantic schema. Templates never contain coordinates, pixel offsets, or SVG -
only descriptive attributes (e.g. ``image_side``, ``orientation``, ``layout``,
``forces``) that the deterministic generators in ``diagram_generators.py``
translate into geometry.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from app.core.exceptions import DataLoadError

logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


class DiagramTemplateService:
    """In-memory access layer over the diagram template JSON files."""

    def __init__(self, templates_dir: Path) -> None:
        self._templates: dict[str, dict] = self._load(templates_dir)
        logger.info(
            "DiagramTemplateService loaded %d diagram templates from %s",
            len(self._templates),
            templates_dir,
        )

    @staticmethod
    def _load(templates_dir: Path) -> dict[str, dict]:
        if not templates_dir.is_dir():
            raise DataLoadError(f"Diagram template directory not found: {templates_dir}")

        templates: dict[str, dict] = {}
        for template_file in sorted(templates_dir.glob("*.json")):
            try:
                raw = json.loads(template_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise DataLoadError(f"Diagram template file is not valid JSON: {template_file}") from exc

            template_id = raw.get("template_id")
            if not template_id:
                raise DataLoadError(f"Diagram template file missing 'template_id': {template_file}")
            templates[template_id] = raw
        return templates

    def get(self, template_id: str) -> dict | None:
        """Return a template by its id, if loaded."""

        return self._templates.get(template_id)

    def all(self) -> dict[str, dict]:
        """Return all loaded templates, keyed by template id."""

        return dict(self._templates)

    def select(self, diagram_type: str, concept: str | None, scenario: str | None) -> tuple[str, dict]:
        """Select the best template for a diagram type/concept.

        Looks up ``{diagram_type}_{concept}``. If no matching template
        exists (unknown/unsupported concept), returns a generic empty
        template so downstream code can still proceed without coordinates.
        """

        if concept:
            template_id = f"{diagram_type}_{_slugify(concept)}"
            template = self._templates.get(template_id)
            if template is not None:
                return template_id, template

        generic_id = f"{diagram_type}_generic"
        return generic_id, {
            "template_id": generic_id,
            "diagram_type": diagram_type,
            "concept": concept,
            "default_scenario": scenario,
            "entities": [],
            "scenario_rules": {},
        }
