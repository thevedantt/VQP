import json
from pathlib import Path
from typing import List, Dict, Any

from utils.logger import logger

class DatasetStatistics:
    """
    Generates summary metrics and statistical distributions for the final unique question set.
    """

    def generate_statistics(self, original_count: int, unique_questions: List[Dict[str, Any]], reports_dir: Path) -> Dict[str, Any]:
        """
        Computes counts by section and type, calculates sums, and saves dataset_statistics.json.
        """
        reports_dir.mkdir(parents=True, exist_ok=True)

        unique_count = len(unique_questions)
        duplicates_removed = original_count - unique_count

        questions_by_section = {}
        questions_by_type = {}

        for q in unique_questions:
            sect = q.get("section", "Unknown")
            q_type = q.get("type", "Unknown")

            questions_by_section[sect] = questions_by_section.get(sect, 0) + 1
            questions_by_type[q_type] = questions_by_type.get(q_type, 0) + 1

        stats = {
            "total_questions_ingested": original_count,
            "unique_questions_count": unique_count,
            "duplicates_removed": duplicates_removed,
            "questions_by_section": questions_by_section,
            "questions_by_type": questions_by_type
        }

        stats_path = reports_dir / "dataset_statistics.json"
        try:
            with open(stats_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=4)
            logger.info(f"Saved dataset statistics to {stats_path}")
        except Exception as e:
            logger.error(f"Failed to save dataset statistics: {str(e)}")

        return stats
