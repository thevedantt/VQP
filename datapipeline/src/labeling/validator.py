import json
import re
from typing import Dict, Any, Optional

from utils.logger import logger

class LabelValidator:
    """
    Validates and standardizes metadata JSON returned by the LLM.
    """

    VALID_DIFFICULTIES = {"easy", "medium", "hard"}
    VALID_DIAGRAM_TYPES = {"free_body", "circuit", "graph", "ray_diagram", "none"}

    def clean_json_response(self, text: str) -> str:
        """Cleans markdown code block wraps and leading/trailing junk from text."""
        cleaned = text.strip()
        # Find JSON object boundary if there is leading/trailing text
        first_bracket = cleaned.find('{')
        last_bracket = cleaned.rfind('}')
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            cleaned = cleaned[first_bracket:last_bracket + 1]
        return cleaned

    def validate_and_parse(self, llm_output: str) -> Optional[Dict[str, Any]]:
        """
        Parses LLM output string, validates required fields, formats values,
        and returns a cleaned Dict. Returns None if parsing or validation fails.
        """
        if not llm_output:
            logger.warning("Empty LLM output response.")
            return None

        cleaned_output = self.clean_json_response(llm_output)

        try:
            data = json.loads(cleaned_output)
        except Exception as e:
            logger.warning(f"JSON parsing failed: {str(e)}")
            return None

        # Verify key presence and non-empty strings
        chapter = data.get("chapter")
        concept = data.get("concept")
        difficulty = data.get("difficulty")
        requires_diagram = data.get("requires_diagram")
        diagram_type = data.get("diagram_type")

        if not chapter or not str(chapter).strip():
            logger.warning("Validation failed: 'chapter' is empty or missing.")
            return None

        if not concept or not str(concept).strip():
            logger.warning("Validation failed: 'concept' is empty or missing.")
            return None

        if difficulty not in self.VALID_DIFFICULTIES:
            logger.warning(f"Validation failed: 'difficulty' value '{difficulty}' is invalid.")
            return None

        if not isinstance(requires_diagram, bool):
            logger.warning("Validation failed: 'requires_diagram' is not a boolean.")
            return None

        if diagram_type not in self.VALID_DIAGRAM_TYPES:
            logger.warning(f"Validation failed: 'diagram_type' value '{diagram_type}' is invalid.")
            return None

        # Return standardized dictionary
        return {
            "chapter": str(chapter).strip(),
            "concept": str(concept).strip(),
            "difficulty": difficulty,
            "requires_diagram": requires_diagram,
            "diagram_type": diagram_type
        }

