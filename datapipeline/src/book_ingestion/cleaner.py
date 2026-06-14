import sys
import re
from pathlib import Path
from typing import List

# Ensure absolute import path works
src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from cleaning.text_cleaner import TextCleaner
from utils.logger import logger

class BookCleaner(TextCleaner):
    """
    Cleaner for NCERT Class 12 Physics textbook text.
    """
    def __init__(self) -> None:
        super().__init__()
        # Additional patterns to remove specific book headers/footers
        self.book_patterns = [
            re.compile(r"Rationalised\s*\d{4}-\d{2}", re.IGNORECASE),
            re.compile(r"Rationalized\s*\d{4}-\d{2}", re.IGNORECASE),
            re.compile(r"^Physics\s*$", re.IGNORECASE),
            re.compile(r"^Class\s*XII\s*$", re.IGNORECASE),
            re.compile(r"^\s*Chapter\s+\d+\s*$", re.IGNORECASE), # running header "Chapter 1"
        ]

    def should_remove_line(self, line: str) -> bool:
        cleaned = line.strip()
        if not cleaned:
            return True

        # Use parent rules (Hindi, PTO, Roll no, page number)
        if super().should_remove_line(line):
            return True

        # Check additional book header/footer patterns
        for pattern in self.book_patterns:
            if pattern.match(cleaned):
                return True

        return False

    def clean_text(self, text: str) -> str:
        """
        Cleans the full text, normalizing whitespaces and filtering lines.
        """
        return self.clean_document_text(text)

    def clean_pages(self, pages: List[str]) -> List[str]:
        """
        Cleans each page individually and returns a list of cleaned page texts.
        """
        cleaned_pages = []
        for i, page in enumerate(pages):
            cleaned_page = self.clean_page(page)
            # If the page has significant text after cleaning, add it
            cleaned_pages.append(cleaned_page)
        return cleaned_pages
