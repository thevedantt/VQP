from typing import List, Dict, Any

class DiagramAnalysis:
    """
    Analyzes the distribution of diagram types across the labeled dataset.
    """

    def analyze(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts counts for free_body, circuit, graph, and ray_diagram questions.
        """
        diagram_qs = [q for q in questions if q.get("requires_diagram")]
        
        counts = {
            "free_body": 0,
            "circuit": 0,
            "graph": 0,
            "ray_diagram": 0
        }

        for q in diagram_qs:
            dtype = q.get("diagram_type", "none").lower()
            if dtype in counts:
                counts[dtype] += 1

        return {
            "total_diagram_questions": len(diagram_qs),
            "free_body": counts["free_body"],
            "circuit": counts["circuit"],
            "graph": counts["graph"],
            "ray_diagram": counts["ray_diagram"]
        }
