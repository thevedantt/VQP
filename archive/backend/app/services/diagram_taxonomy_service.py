"""Loads the static physics diagram taxonomy (types -> concepts -> scenarios).

The taxonomy JSON files under ``data/diagram_taxonomy/`` describe, per
``diagram_type``, the recognized physics concepts, their scenarios, and the
keyword triggers used to identify them from question text. This taxonomy
drives both the vocabulary offered to the LLM in
``PhysicsAnalyzerService`` prompts and the local keyword-matching fallback
when no LLM is available.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.core.exceptions import DataLoadError

logger = logging.getLogger(__name__)


class DiagramTaxonomyService:
    """In-memory access layer over the diagram taxonomy JSON files."""

    def __init__(self, taxonomy_dir: Path) -> None:
        self._taxonomies: dict[str, dict] = self._load(taxonomy_dir)
        logger.info(
            "DiagramTaxonomyService loaded %d diagram-type taxonomies from %s",
            len(self._taxonomies),
            taxonomy_dir,
        )

    @staticmethod
    def _load(taxonomy_dir: Path) -> dict[str, dict]:
        if not taxonomy_dir.is_dir():
            raise DataLoadError(f"Diagram taxonomy directory not found: {taxonomy_dir}")

        taxonomies: dict[str, dict] = {}
        for taxonomy_file in sorted(taxonomy_dir.glob("*.json")):
            try:
                raw = json.loads(taxonomy_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise DataLoadError(f"Diagram taxonomy file is not valid JSON: {taxonomy_file}") from exc

            diagram_type = raw.get("diagram_type")
            if not diagram_type:
                raise DataLoadError(f"Diagram taxonomy file missing 'diagram_type': {taxonomy_file}")
            taxonomies[diagram_type] = raw
        return taxonomies

    def get(self, diagram_type: str) -> dict | None:
        """Return the full taxonomy entry for a diagram type, if any."""

        return self._taxonomies.get(diagram_type)

    def all(self) -> dict[str, dict]:
        """Return all loaded taxonomies, keyed by diagram type."""

        return dict(self._taxonomies)

    def get_concept_entry(self, diagram_type: str, concept: str) -> dict | None:
        """Return the taxonomy entry for a specific concept, if any."""

        taxonomy = self._taxonomies.get(diagram_type)
        if not taxonomy:
            return None
        return taxonomy.get("concepts", {}).get(concept)

    def match_concept(self, diagram_type: str, text: str) -> tuple[str, str] | None:
        """Match question text against a diagram type's concepts/scenarios.

        Returns ``(concept, scenario)`` for the first concept whose triggers
        appear in ``text``, with the scenario refined by matching
        ``scenario_triggers`` (falling back to the concept's
        ``default_scenario``). Returns ``None`` if no concept matches.
        """

        taxonomy = self._taxonomies.get(diagram_type)
        if not taxonomy:
            return None

        text_lower = text.lower()
        for concept_name, concept in taxonomy.get("concepts", {}).items():
            triggers = concept.get("triggers", [])
            if not any(trigger in text_lower for trigger in triggers):
                continue

            scenario = concept.get("default_scenario")
            for scenario_name, phrases in concept.get("scenario_triggers", {}).items():
                if any(phrase in text_lower for phrase in phrases):
                    scenario = scenario_name
                    break

            return concept_name, scenario

        return None

    def prompt_vocabulary(self) -> str:
        """Render a compact diagram_type -> concept -> scenarios listing for LLM prompts."""

        lines: list[str] = []
        for diagram_type, taxonomy in self._taxonomies.items():
            concept_lines = []
            for concept_name, concept in taxonomy.get("concepts", {}).items():
                scenarios = ", ".join(concept.get("scenarios", []))
                concept_lines.append(f"{concept_name} (scenarios: {scenarios})")
            lines.append(f"{diagram_type}: " + "; ".join(concept_lines))
        return "\n".join(lines)
