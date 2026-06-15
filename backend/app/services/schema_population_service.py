"""Deterministic schema population layer - the "Diagram Generator" half of the split.

    Question -> PhysicsAnalyzer -> Dynamic Semantic Schema -> Template Selection
             -> SchemaPopulationService -> Render Schema -> SVG

Pure code, no LLM involvement: combines a ``PhysicsAnalysis`` (the dynamic,
concept-specific semantic schema) with a selected template's categorical
``scenario_rules`` to produce a render schema, then dispatches to the
existing ``diagram_generators.py`` generators to compute the actual
coordinates/geometry that ``diagram_svg.render_svg`` consumes.
"""

from __future__ import annotations

from app.services.diagram_generators import DIAGRAM_GENERATORS
from app.services.physics_analyzer_service import PhysicsAnalysis

_EMPTY_CANVAS = {"width": 800, "height": 400}


class SchemaPopulationService:
    """Builds the dynamic semantic schema and render schema from a physics analysis."""

    @staticmethod
    def build_semantic_schema(analysis: PhysicsAnalysis, template_id: str, template: dict) -> dict:
        """Return the dynamic, concept-specific semantic schema as a plain dict.

        Still purely descriptive - no coordinates. ``required_entities`` falls
        back to the selected template's ``entities`` if the analysis didn't
        identify any.
        """

        required_entities = analysis.required_entities or list(template.get("entities", []))

        return {
            "chapter": analysis.chapter,
            "concept": analysis.concept,
            "scenario": analysis.scenario,
            "diagram_type": analysis.diagram_type,
            "diagram_required": analysis.diagram_required,
            "confidence": analysis.confidence,
            "candidate_concepts": analysis.candidate_concepts,
            "required_entities": required_entities,
            "relationships": analysis.relationships,
            "constraints": analysis.constraints,
            "visual_rules": analysis.visual_rules,
            "validation": analysis.validation,
            "extra": analysis.extra,
            "template_id": template_id,
        }

    @staticmethod
    def build_render_schema(semantic_schema: dict, question_text: str, template: dict) -> dict:
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

        scenario_rules = template.get("scenario_rules", {})
        scenario = semantic_schema.get("scenario")
        rules = scenario_rules.get(scenario) or scenario_rules.get(template.get("default_scenario")) or {}

        return generator(
            question_text,
            entities=semantic_schema.get("required_entities"),
            scenario=scenario,
            rules=rules,
            concept=semantic_schema.get("concept"),
            extra=semantic_schema.get("extra"),
        )
