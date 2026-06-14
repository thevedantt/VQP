import re
from typing import List, Union

class TextCleaner:
    """
    Cleans extracted text from CBSE Physics PDFs by removing Hindi text,
    headers, footers, page numbers, Roll No blocks, PTO, and normalizing whitespace.
    """

    def __init__(self):
        # Compiled regex patterns for efficiency
        self.devanagari_pattern = re.compile(r"[\u0900-\u097f]")
        
        # Roll No and Q.P. Code patterns
        self.roll_no_patterns = [
            re.compile(r"roll\s*no", re.IGNORECASE),
            re.compile(r"candidate", re.IGNORECASE),
            re.compile(r"title\s*page\s*of\s*the\s*answer", re.IGNORECASE),
            re.compile(r"q\.?\s*p\.?\s*code", re.IGNORECASE),
        ]
        
        # Series/Set/Code patterns
        self.header_patterns = [
            re.compile(r"series\s*:\s*\w+", re.IGNORECASE),
            re.compile(r"set\s*~\s*\d+", re.IGNORECASE),
            re.compile(r"\*[a-z0-9]+\*", re.IGNORECASE),
            re.compile(r"~\d+/\d+/\d+~", re.IGNORECASE), # e.g. ~55/3/1~
            re.compile(r"\b\d+/\d+/\d+\b"),              # e.g. 55/3/1
        ]
        
        # Page numbers and PTO
        self.pto_pattern = re.compile(r"\bp\.?\s*t\.?\s*o\.?\b", re.IGNORECASE)
        self.page_num_pattern = re.compile(r"^\s*\d+\s*(?:•|\*|)\s*$")

    def contains_hindi(self, text: str, threshold: int = 3) -> bool:
        """Checks if the text contains Hindi (Devanagari) characters above a threshold count."""
        return len(self.devanagari_pattern.findall(text)) >= threshold

    def clean_line(self, line: str) -> str:
        """Cleans individual line formatting and corrupted characters."""
        # Remove corrupted characters (e.g. \ufffd, control chars except \n, \t)
        line = ''.join(c for c in line if c != '\ufffd' and (ord(c) >= 32 or c in '\n\t'))
        
        # Replace odd spaces/bullet symbols if needed
        line = re.sub(r'\s+', ' ', line)
        return line.strip()

    def should_remove_line(self, line: str) -> bool:
        """Determines if a line matches any of the patterns that need to be removed."""
        cleaned = line.strip()
        if not cleaned:
            return True
            
        # Remove lines containing Hindi characters
        if self.contains_hindi(cleaned, threshold=1):
            return True

        # Remove PTO
        if self.pto_pattern.search(cleaned):
            return True

        # Remove Roll No patterns
        if any(pat.search(cleaned) for pat in self.roll_no_patterns):
            return True

        # Remove Series/Set/Code patterns
        if any(pat.search(cleaned) for pat in self.header_patterns):
            return True

        # Remove Page numbers
        if self.page_num_pattern.match(cleaned):
            return True

        return False

    def clean_page(self, page_text: str) -> str:
        """Cleans text of a single page if it is not a Hindi page."""
        if self.contains_hindi(page_text, threshold=5):
            return "" # Discard entire Hindi page
            
        cleaned_lines = []
        for line in page_text.splitlines():
            if self.should_remove_line(line):
                continue
            cleaned = self.clean_line(line)
            if cleaned:
                cleaned_lines.append(cleaned)
                
        return "\n".join(cleaned_lines)

    def clean_document_pages(self, pages: List[str]) -> str:
        """Cleans a list of page texts, discarding Hindi pages and cleaning English ones."""
        cleaned_pages = []
        for page_text in pages:
            cleaned = self.clean_page(page_text)
            if cleaned:
                cleaned_pages.append(cleaned)
                
        # Combine pages and normalize multiple empty lines
        combined = "\n\n".join(cleaned_pages)
        combined = re.sub(r'\n{3,}', '\n\n', combined)
        return combined.strip()

    def clean_document_text(self, full_text: str) -> str:
        """Fallback cleaner if page-by-page list is not available."""
        # Attempt to split by form-feed (if exists) or clean line-by-line
        pages = full_text.split('\x0c') # Form feed often separates pages
        if len(pages) > 1:
            return self.clean_document_pages(pages)
            
        # Line-by-line fallback
        cleaned_lines = []
        for line in full_text.splitlines():
            if self.should_remove_line(line):
                continue
            cleaned = self.clean_line(line)
            if cleaned:
                cleaned_lines.append(cleaned)
        
        combined = "\n".join(cleaned_lines)
        combined = re.sub(r'\n{3,}', '\n\n', combined)
        return combined.strip()
