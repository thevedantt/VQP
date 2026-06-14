import json
from pathlib import Path
from typing import List, Dict, Any
from utils.logger import logger

class BookStatistics:
    """
    Generates statistics from the processed textbook chapters.
    """
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)

    def generate(self, chapters: List[Dict[str, Any]], total_pages_processed: int) -> Dict[str, Any]:
        """
        Computes statistics, saves them to book_statistics.json, and returns the data.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stats_path = self.output_dir / "book_statistics.json"

        total_words = sum(ch["word_count"] for ch in chapters)
        chapter_dist = {ch["chapter_name"]: ch["word_count"] for ch in chapters}

        stats_data = {
            "total_chapters": len(chapters),
            "total_words": total_words,
            "total_pages_processed": total_pages_processed,
            "chapter_word_distribution": chapter_dist
        }

        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved book statistics to {stats_path}")

        return stats_data
