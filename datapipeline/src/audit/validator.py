from typing import List, Dict, Any

from utils.logger import logger

class MetadataAuditValidator:
    """
    Scans the labeled dataset to find metadata discrepancies, quality flags, and inconsistencies.
    """

    VALID_CHAPTERS = {
        "Electric Charges and Fields",
        "Electrostatic Potential and Capacitance",
        "Current Electricity",
        "Moving Charges and Magnetism",
        "Magnetism and Matter",
        "Electromagnetic Induction",
        "Alternating Current",
        "Electromagnetic Waves",
        "Ray Optics",
        "Wave Optics",
        "Dual Nature of Radiation and Matter",
        "Atoms",
        "Nuclei",
        "Semiconductor Electronics"
    }

    def audit_quality(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans all labeled questions and flags any with issues.
        """
        flags = []

        for q in questions:
            q_id = q.get("question_id", "unknown")
            chapter = q.get("chapter", "")
            concept = q.get("concept", "")
            requires_diagram = q.get("requires_diagram", False)
            diagram_type = q.get("diagram_type", "none")
            difficulty = q.get("difficulty", "")

            issues = []

            # 1. Empty concepts
            if not concept or not str(concept).strip() or str(concept).lower() == "general":
                issues.append("Empty or generic concept field")

            # 2. Suspicious chapter assignments
            if chapter not in self.VALID_CHAPTERS:
                issues.append(f"Suspicious chapter assignment: '{chapter}'")

            # 3. Diagram mismatch: type != none but requires_diagram = false
            if diagram_type != "none" and not requires_diagram:
                issues.append(f"Diagram type is '{diagram_type}' but requires_diagram is false")

            # 4. Diagram mismatch: type == none but requires_diagram = true
            if requires_diagram and diagram_type == "none":
                issues.append("requires_diagram is true but diagram_type is 'none'")

            # 5. Invalid difficulty
            if difficulty not in {"easy", "medium", "hard"}:
                issues.append(f"Invalid difficulty value: '{difficulty}'")

            if issues:
                flags.append({
                    "question_id": q_id,
                    "issues": issues,
                    "record": {
                        "question": q.get("question")[:100] + "...",
                        "chapter": chapter,
                        "concept": concept,
                        "difficulty": difficulty,
                        "requires_diagram": requires_diagram,
                        "diagram_type": diagram_type
                    }
                })
                logger.warning(f"Quality Flag for {q_id}: {issues}")

        return flags
