"""Diagram routing layer (Phase 4).

Routes a populated semantic schema to the appropriate specialized physics
engine, falling back to the legacy hand-rolled ``DIAGRAM_GENERATORS`` +
``diagram_svg.render_svg`` pipeline when no specialized engine applies (or
the specialized engine fails):

    Semantic Schema -> DiagramRouter -> Generator Input -> Render Schema -> SVG
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.services import magnetic_field_engine, magnetic_field_renderer
from app.services.diagram_generators import DIAGRAM_GENERATORS
from app.services.diagram_svg import render_svg

logger = logging.getLogger(__name__)

_EMPTY_CANVAS = {"width": 800, "height": 400}

# magnetic_field concepts with a dedicated Magpylib engine (Phase 5). Other
# magnetic_field concepts, and every other diagram type, use the legacy path.
_MAGPYLIB_MAGNETIC_FIELD_CONCEPTS = {"solenoid", "toroid", "circular_loop", "straight_wire", "bar_magnet"}


@dataclass(frozen=True)
class RouterResult:
    """The outcome of routing a semantic schema to a diagram engine."""

    engine: str
    generator_input: dict[str, Any]
    render_schema: dict[str, Any]
    svg: str


class DiagramRouter:
    """Routes a semantic schema to the correct specialized physics engine."""

    def generate(self, semantic_schema: dict[str, Any], question_text: str, template: dict[str, Any]) -> RouterResult:
        diagram_type = semantic_schema.get("diagram_type")
        generator_input = self._build_generator_input(semantic_schema, template)

        if diagram_type == "magnetic_field" and self._resolve_source_type(semantic_schema) in _MAGPYLIB_MAGNETIC_FIELD_CONCEPTS:
            try:
                render_schema = magnetic_field_engine.generate(semantic_schema, generator_input, question_text)
                svg = magnetic_field_renderer.render(render_schema)
                if svg:
                    return RouterResult("magpylib_magnetic_field", generator_input, render_schema, svg)
            except Exception as exc:  # pragma: no cover - depends on magpylib runtime
                logger.warning("Magpylib magnetic field engine failed, falling back to legacy: %s", exc)

        return self._legacy(diagram_type, generator_input, question_text)

    @staticmethod
    def _resolve_source_type(semantic_schema: dict[str, Any]) -> str | None:
        """Identify the magnetic-field source type, mirroring the resolution
        order used by ``magnetic_field_engine.generate``.

        The LLM sometimes returns a generic ``concept`` (e.g. ``"magnetic_field"``)
        while still pinpointing the specific source via ``geometry_rules``/``extra``
        - check those first so Magpylib is used whenever it can be.
        """

        extra = semantic_schema.get("extra") or {}
        geometry_rules = semantic_schema.get("geometry_rules") or {}
        return geometry_rules.get("source_type") or extra.get("source_type") or extra.get("source") or semantic_schema.get("concept")

    @staticmethod
    def _legacy(diagram_type: str | None, generator_input: dict[str, Any], question_text: str) -> RouterResult:
        generator = DIAGRAM_GENERATORS.get(diagram_type or "")
        if generator is None:
            render_schema = {
                "diagram_type": diagram_type or "none",
                "title": "No Diagram",
                "canvas": dict(_EMPTY_CANVAS),
                "components": [],
                "connections": [],
                "labels": [],
                "metadata": {},
            }
        else:
            render_schema = generator(question_text, **generator_input)

        svg = render_svg(render_schema)
        return RouterResult("legacy", generator_input, render_schema, svg)

    @staticmethod
    def _build_generator_input(semantic_schema: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
        """Assemble the categorical inputs the diagram generators expect.

        Moved from the former ``SchemaPopulationService.build_render_schema``.
        """

        scenario_rules = template.get("scenario_rules", {})
        scenario = semantic_schema.get("scenario")
        rules = scenario_rules.get(scenario) or scenario_rules.get(template.get("default_scenario")) or {}

        return {
            "entities": semantic_schema.get("required_entities"),
            "scenario": scenario,
            "rules": rules,
            "concept": semantic_schema.get("concept"),
            "extra": semantic_schema.get("extra"),
        }
