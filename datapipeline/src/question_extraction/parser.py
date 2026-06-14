import re
from typing import Dict, Tuple, Optional

class QuestionParser:
    """
    Utility parser to handle MCQ options parsing, cleaning,
    and structured text preprocessing.
    """

    def __init__(self):
        # Match option format (A) or (B) or (C) or (D) at start of line
        self.option_pattern = re.compile(r"^\s*\(([A-D])\)\s*(.*)$")

    def parse_option_line(self, line: str) -> Optional[Tuple[str, str]]:
        """
        Tries to parse a line as an option.
        Returns tuple of (option_letter, text) if matches, else None.
        """
        match = self.option_pattern.match(line)
        if match:
            return match.group(1), match.group(2).strip()
        return None

    def clean_text(self, text: str) -> str:
        """Standardizes line spacing, trims whitespace, and normalizes spacing."""
        if not text:
            return ""
        # Replace multiple spaces with a single space, maintaining linebreaks
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join(lines)
        return re.sub(r'[ \t]+', ' ', cleaned).strip()
