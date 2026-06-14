import re
from typing import List, Dict, Any
from utils.logger import logger

class ChapterDetector:
    """
    Detects chapters dynamically from cleaned book pages.
    """
    def __init__(self) -> None:
        self.expected_chapters = {
            1: "Electric Charges and Fields",
            2: "Electrostatic Potential and Capacitance",
            3: "Current Electricity",
            4: "Moving Charges and Magnetism",
            5: "Magnetism and Matter",
            6: "Electromagnetic Induction",
            7: "Alternating Current",
            8: "Electromagnetic Waves"
        }
        
        # Regex to match X.1 INTRODUCTION / Introduction
        self.intro_pattern = re.compile(r"\b(\d+)\.1\s+INTRODUCTION\b", re.IGNORECASE)
        # Regex to match "Chapter Eight", "Chapter One" etc.
        self.chapter_word_pattern = re.compile(
            r"\bChapter\s+(One|Two|Three|Four|Five|Six|Seven|Eight)\b", re.IGNORECASE
        )
        self.word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8
        }

    def detect(self, pages: List[str]) -> List[Dict[str, Any]]:
        """
        Scans pages to detect chapters and their starting page indices.
        Returns a list of dicts:
        [
            {
                "chapter_number": int,
                "chapter_name": str,
                "start_page_idx": int
            },
            ...
        ]
        """
        detected = []
        seen_chapters = set()

        # Skip first 4 pages (index 0 to 3) to avoid Table of Contents matches
        for idx in range(4, len(pages)):
            page_text = pages[idx]
            if not page_text.strip():
                continue

            chapter_num = None

            # Try matching X.1 INTRODUCTION
            intro_match = self.intro_pattern.search(page_text)
            if intro_match:
                chapter_num = int(intro_match.group(1))

            # If not found, try matching "Chapter [Word]"
            if not chapter_num:
                word_match = self.chapter_word_pattern.search(page_text)
                if word_match:
                    word = word_match.group(1).lower()
                    chapter_num = self.word_to_num.get(word)

            if chapter_num and chapter_num not in seen_chapters:
                # Ensure chapter number is within the range of expected chapters (1-8)
                if chapter_num in self.expected_chapters:
                    chapter_name = self.expected_chapters[chapter_num]
                    logger.info(f"Detected Chapter {chapter_num}: '{chapter_name}' starting at page {idx + 1}")
                    detected.append({
                        "chapter_number": chapter_num,
                        "chapter_name": chapter_name,
                        "start_page_idx": idx
                    })
                    seen_chapters.add(chapter_num)

        # Sort detected chapters by number to ensure they are sequential
        detected.sort(key=lambda x: x["chapter_number"])
        return detected
