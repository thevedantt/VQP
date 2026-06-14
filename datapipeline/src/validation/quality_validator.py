import json
import re
from pathlib import Path
from typing import Dict, Any

from utils.logger import logger

class QualityValidator:
    """
    Validates text quality by calculating character count, word count,
    readability score, and corruption percentage, then assigning a status.
    """

    def calculate_readability(self, text: str) -> int:
        """Calculates a heuristic readability score (0-100) based on sentence and word lengths."""
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        
        if word_count == 0 or char_count == 0:
            return 0

        # Split sentences using common ending punctuations
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)

        avg_sent_len = word_count / max(1, sentence_count)
        avg_word_len = char_count / max(1, word_count)

        # Formula where longer sentences and words decrease readability
        score = 100 - (avg_sent_len * 0.35) - (avg_word_len * 7.5)
        return int(max(0, min(100, score)))

    def calculate_corruption(self, text: str) -> float:
        """Calculates percentage of corrupted/replacement characters in text."""
        char_count = len(text)
        if char_count == 0:
            return 0.0

        # Count \ufffd (replacement character) and control characters excluding standard whitespaces
        corrupted_count = sum(1 for c in text if c == '\ufffd' or (ord(c) < 32 and c not in '\n\r\t'))
        return round((corrupted_count / char_count) * 100, 4)

    def determine_status(self, readability: int, corruption: float, word_count: int) -> str:
        """Determines status of the text file based on metrics."""
        if word_count < 50 or corruption > 1.0 or readability < 30:
            return "Poor"
        elif corruption > 0.1 or readability < 55:
            return "Needs Cleaning"
        elif readability >= 70 and corruption == 0.0:
            return "Excellent"
        else:
            return "Good"

    def validate(self, text: str, file_name: str, reports_dir: Path) -> Dict[str, Any]:
        """
        Validates clean text, generates a report, and saves it to reports_dir.
        """
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        
        readability = self.calculate_readability(text)
        corruption = self.calculate_corruption(text)
        status = self.determine_status(readability, corruption, word_count)

        report = {
            "file_name": file_name,
            "character_count": char_count,
            "word_count": word_count,
            "readability_score": readability,
            "corruption_percentage": corruption,
            "status": status
        }

        # Save individual JSON report
        report_path = reports_dir / f"{Path(file_name).stem}_report.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4)
            logger.info(f"Saved quality report to {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report for {file_name}: {str(e)}")

        return report
