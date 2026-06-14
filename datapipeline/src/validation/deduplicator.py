import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Dict, Any

from utils.logger import logger

class QuestionDeduplicator:
    """
    Detects and filters duplicate questions using exact, normalized, and fuzzy text matches.
    """

    def __init__(self, fuzzy_threshold: float = 0.90):
        self.fuzzy_threshold = fuzzy_threshold

    def normalize_text(self, text: str) -> str:
        """Removes all non-alphanumeric characters and lowercases the text."""
        if not text:
            return ""
        # Keep letters and digits, lowercase it, remove spaces
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', text)
        return cleaned.lower()

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculates textual similarity ratio using SequenceMatcher."""
        return SequenceMatcher(None, s1, s2).ratio()

    def deduplicate(self, questions: List[Dict[str, Any]], reports_dir: Path, questions_dir: Path) -> List[Dict[str, Any]]:
        """
        Deduplicates questions and saves unique_questions.json and deduplication_report.json.
        """
        reports_dir.mkdir(parents=True, exist_ok=True)
        questions_dir.mkdir(parents=True, exist_ok=True)

        unique_questions = []
        duplicates = []

        for q in questions:
            q_text = q.get("question", "")
            norm_text = self.normalize_text(q_text)
            
            is_duplicate = False
            duplicate_reason = ""
            matched_with = None

            for uq in unique_questions:
                uq_text = uq.get("question", "")
                
                # 1. Exact match
                if q_text == uq_text:
                    is_duplicate = True
                    duplicate_reason = "Exact Match"
                    matched_with = uq
                    break
                
                # 2. Normalized text match
                uq_norm = self.normalize_text(uq_text)
                if norm_text == uq_norm:
                    is_duplicate = True
                    duplicate_reason = "Normalized Match"
                    matched_with = uq
                    break
                
                # 3. Fuzzy similarity match
                # Only run fuzzy comparison if lengths are reasonably close to optimize
                len_ratio = min(len(norm_text), len(uq_norm)) / max(1, len(norm_text), len(uq_norm))
                if len_ratio > 0.8:
                    sim = self.calculate_similarity(norm_text, uq_norm)
                    if sim >= self.fuzzy_threshold:
                        is_duplicate = True
                        duplicate_reason = f"Fuzzy Match (similarity: {sim:.4f})"
                        matched_with = uq
                        break

            if is_duplicate:
                duplicates.append({
                    "removed_question": {
                        "question_no": q.get("question_no"),
                        "source_file": q.get("source_file"),
                        "question": q_text
                    },
                    "kept_question": {
                        "question_no": matched_with.get("question_no"),
                        "source_file": matched_with.get("source_file"),
                        "question": matched_with.get("question")
                    },
                    "reason": duplicate_reason
                })
                logger.info(f"Duplicate found: Q{q.get('question_no')} in {q.get('source_file')} is a {duplicate_reason} of Q{matched_with.get('question_no')} in {matched_with.get('source_file')}")
            else:
                unique_questions.append(q)

        # Save unique_questions.json
        unique_path = questions_dir / "unique_questions.json"
        try:
            with open(unique_path, "w", encoding="utf-8") as f:
                json.dump(unique_questions, f, indent=4)
            logger.info(f"Saved unique questions to {unique_path}")
        except Exception as e:
            logger.error(f"Failed to save unique questions: {str(e)}")

        # Save deduplication_report.json
        report = {
            "original_count": len(questions),
            "unique_count": len(unique_questions),
            "duplicates_removed_count": len(duplicates),
            "duplicates_removed": duplicates
        }
        
        report_path = reports_dir / "deduplication_report.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4)
            logger.info(f"Saved deduplication report to {report_path}")
        except Exception as e:
            logger.error(f"Failed to save deduplication report: {str(e)}")

        return unique_questions
