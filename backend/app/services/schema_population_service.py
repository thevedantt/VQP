"""Deterministic schema population layer - the "Diagram Generator" half of the split.

    Question -> PhysicsAnalyzer -> Semantic Diagram JSON -> Template Selection
             -> SchemaPopulationService -> Render JSON -> SVG

Pure code, no LLM involvement: combines a ``PhysicsAnalysis`` (concept,
scenario, entities) with a selected template's categorical
``scenario_rules`` to produce a semantic schema, then dispatches to the
existing ``diagram_generators.py`` generators to compute the actual
coordinates/geometry (``render schema``) that ``diagram_svg.render_svg``
consumes.
"""

from __future__ import annotations

from app.services.diagram_generators import DIAGRAM_GENERATORS
from app.services.physics_analyzer_service import PhysicsAnalysis

_EMPTY_CANVAS = {"width": 800, "height": 400}


class SchemaPopulationService:
    """Builds semantic and render schemas deterministically from a physics analysis."""

    @staticmethod
    def build_semantic_schema(analysis: PhysicsAnalysis, template_id: str, template: dict) -> dict:
        """Merge a template's scenario rules with the physics analysis.

        Still purely descriptive - no coordinates. ``scenario`` falls back to
        the template's ``default_scenario`` if the analyzed scenario isn't a
        recognized key in ``scenario_rules``.
        """

        scenario_rules = template.get("scenario_rules", {})
        scenario = analysis.scenario if analysis.scenario in scenario_rules else template.get("default_scenario")
        rules = scenario_rules.get(scenario, {}) if scenario else {}

        entities = analysis.entities or list(template.get("entities", []))

        return {
            "diagram_type": analysis.diagram_type,
            "concept": analysis.concept,
            "scenario": scenario,
            "template_id": template_id,
            "entities": entities,
            "rules": rules,
        }

    @staticmethod
    def build_render_schema(semantic_schema: dict, question_text: str) -> dict:
        """Dispatch to the deterministic diagram generators to compute geometry."""

        diagram_type = semantic_schema.get("diagram_type")
        generator = DIAGRAM_GENERATORS.get(diagram_type)
        if generator is None:
            return {
                "diagram_type": diagram_type or "none",
                "title": "No Diagram",
                "canvas": dict(_EMPTY_CANVAS),
                "components": [],
                "connections": [],
                "labels": [],
                "metadata": {},
            }

        return generator(
            question_text,
            entities=semantic_schema.get("entities"),
            scenario=semantic_schema.get("scenario"),
            rules=semantic_schema.get("rules"),
            concept=semantic_schema.get("concept"),
        )
