import json


class DiagramClassifier:

    def classify(self, question: str):

        q = question.lower()

        if "lens" in q:
            return {
                "diagram_type": "ray",
                "concept": "convex_lens",
                "scenario": "between_f_and_2f"
            }

        if "rlc" in q:
            return {
                "diagram_type": "circuit",
                "concept": "series_rlc",
                "scenario": "ac_source_with_RLC_in_series"
            }

        return {
            "diagram_type": "unknown",
            "concept": "unknown",
            "scenario": "unknown"
        }