import sys
from pathlib import Path

src_root = Path(__file__).resolve().parents[1] / "src"
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from extraction.pdf_extractor import PDFExtractor
import re

pdf_path = Path("C:/CODES/VQP/datapipeline/data/NCERT-Class-12-Physics-Part-1.pdf")
extractor = PDFExtractor()
res = extractor.extract_pdf(pdf_path)
pages = res["pages"]

chapter_words = ["one", "two", "three", "four", "five", "six", "seven", "eight"]
chapters_metadata = []

for idx, page in enumerate(pages):
    # Search for "Chapter One", "Chapter Two", etc.
    # Often formatted as: "Chapter One\n" or "Chapter\nOne"
    # Let's clean up whitespace in search
    cleaned_page_text = " ".join(page.split())
    for num_word in chapter_words:
        pattern = rf"\bChapter\s+{num_word}\b"
        match = re.search(pattern, cleaned_page_text, re.IGNORECASE)
        if match:
            # Check if this is the table of contents or the actual chapter start
            # Actual chapter start will not have dot leaders like "1.1 Introduction... 1" or page numbers following it immediately
            # Let's print context
            print(f"Page {idx+1} matches '{pattern}':")
            print("  Context:", cleaned_page_text[:300])
            print("-" * 50)
