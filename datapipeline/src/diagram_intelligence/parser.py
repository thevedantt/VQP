import json
import re
from typing import Dict, Any, Optional

from utils.logger import logger

class DiagramResponseParser:
    """
    Cleans and validates LLM responses for the diagram intelligence schema.
    """

    VALID_TYPES = {"free_body", "circuit", "graph", "ray_diagram", "optical_instrument", "magnetic_field", "none"}

    def clean_json_response(self, text: str) -> str:
        cleaned = text.strip()
        # Find JSON object boundaries
        first_bracket = cleaned.find('{')
        last_bracket = cleaned.rfind('}')
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            cleaned = cleaned[first_bracket:last_bracket + 1]
        return cleaned

    def parse_and_validate(self, llm_output: str) -> Optional[Dict[str, Any]]:
        """
        Parses LLM response, validates types, and returns structured data or None.
        """
        if not llm_output:
            return None

        cleaned = self.clean_json_response(llm_output)

        try:
            data = json.loads(cleaned)
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {str(e)}")
            return None

        requires_diagram = data.get("requires_diagram")
        diagram_type = data.get("diagram_type")
        confidence = data.get("confidence")
        reason = data.get("reason", "")

        # Check types
        if not isinstance(requires_diagram, bool):
            logger.warning("requires_diagram is not a boolean.")
            return None

        if diagram_type not in self.VALID_TYPES:
            logger.warning(f"diagram_type '{diagram_type}' is invalid.")
            return None

        try:
            confidence = float(confidence)
        except (ValueError, TypeError):
            logger.warning(f"confidence '{confidence}' is not a number.")
            return None

        return {
            "requires_diagram": requires_diagram,
            "diagram_type": diagram_type,
            "confidence": confidence,
            "reason": str(reason).strip()
        }
