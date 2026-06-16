"""Dynamic semantic schema assembly (Phase 3).

    Question -> PhysicsAnalyzer -> Dynamic Semantic Schema -> Template Selection
             -> SchemaPopulationService -> DiagramRouter -> Render Schema -> SVG

Pure code, no LLM involvement: combines a ``PhysicsAnalysis`` (the dynamic,
concept-specific semantic schema) with a selected template's categorical
``entities`` into a single self-contained dict that ``DiagramRouter`` and
``DiagramValidationService`` consume.
"""

from __future__ import annotations

from dataclasses import asdict

from app.services.physics_understanding_service import PhysicsAnalysis


class SchemaPopulationService:
    """Builds the dynamic, concept-specific semantic schema from a physics analysis."""

    @staticmethod
    def build_semantic_schema(analysis: PhysicsAnalysis, template_id: str, template: dict) -> dict:
        """Return the dynamic, concept-specific semantic schema as a plain dict.

        Still purely descriptive - no coordinates. ``required_entities`` falls
        back to the selected template's ``entities`` if the analysis didn't
        identify any, and ``labels`` falls back to ``required_entities``.
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
            "labels": analysis.labels or required_entities,
            "geometry_rules": analysis.geometry_rules,
            "visual_rules": analysis.visual_rules,
            "validation": analysis.validation,
            "understanding": asdict(analysis.understanding),
            "extra": analysis.extra,
            "textbook_context": analysis.textbook_context,
            "template_id": template_id,
        }
