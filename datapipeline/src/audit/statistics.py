from typing import List, Dict, Any

class MetadataStatistics:
    """
    Computes overall distributions for chapters, concepts, and diagram counts across the labeled dataset.
    """

    def calculate_stats(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates counts by chapter, concept, and diagram requirements.
        """
        total_labeled = len(questions)
        diagram_count = sum(1 for q in questions if q.get("requires_diagram"))
        non_diagram_count = total_labeled - diagram_count

        chapter_dist = {}
        concept_dist = {}

        for q in questions:
            ch = q.get("chapter", "Unknown")
            con = q.get("concept", "General")

            chapter_dist[ch] = chapter_dist.get(ch, 0) + 1
            concept_dist[con] = concept_dist.get(con, 0) + 1

        return {
            "total_labeled_questions": total_labeled,
            "diagram_questions": diagram_count,
            "non_diagram_questions": non_diagram_count,
            "chapter_distribution": chapter_dist,
            "concept_distribution": concept_dist
        }
