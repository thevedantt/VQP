import json
import re
from pathlib import Path
from typing import List, Dict, Any
from utils.logger import logger

class Exporter:
    """
    Exports the structured chapter content and index to the output directory.
    """
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.chapters_dir = self.output_dir / "chapters"

    def _sanitize_filename(self, name: str) -> str:
        """Converts a string to a safe lowercase snake_case filename."""
        # Lowercase and replace non-alphanumeric characters with underscores
        s = name.lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s.strip("_")

    def export(self, chapters: List[Dict[str, Any]]) -> None:
        """
        Exports knowledge base, individual chapter files, and the chapter index.
        """
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chapters_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save physics_part1_knowledge_base.json
        kb_path = self.output_dir / "physics_part1_knowledge_base.json"
        kb_data = {
            "book": "NCERT Physics Class 12 Part 1",
            "total_chapters": len(chapters),
            "chapters": chapters
        }
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved knowledge base to {kb_path}")

        # 2. Save individual chapter files
        for ch in chapters:
            sanitized_name = self._sanitize_filename(ch["chapter_name"])
            filename = f"chapter_{ch['chapter_number']:02d}_{sanitized_name}.json"
            ch_path = self.chapters_dir / filename
            
            with open(ch_path, "w", encoding="utf-8") as f:
                json.dump(ch, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved chapter file to {ch_path}")

        # 3. Save chapter_index.json
        index_path = self.output_dir / "chapter_index.json"
        index_data = {}
        for ch in chapters:
            index_data[ch["chapter_name"]] = {
                "chapter_number": ch["chapter_number"],
                "word_count": ch["word_count"]
            }
            
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved chapter index to {index_path}")
