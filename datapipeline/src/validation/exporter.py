import json
from pathlib import Path
from typing import List, Dict, Any

from utils.logger import logger

class FinalDatasetExporter:
    """
    Exports the validated, deduplicated, and formatted unique dataset
    to the backend data folder for ingestion by backend APIs.
    """

    def export(self, unique_questions: List[Dict[str, Any]], export_dir: Path) -> Path:
        """
        Saves final_dataset.json to the specified backend directory.
        """
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / "final_dataset.json"

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(unique_questions, f, indent=4)
            logger.info(f"Successfully exported final dataset to {export_path}")
        except Exception as e:
            logger.error(f"Failed to export final dataset: {str(e)}")

        return export_path
