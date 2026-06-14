import sys
from pathlib import Path

# Ensure absolute import path works
src_root = Path(__file__).resolve().parents[1] / "src"
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from extraction.pdf_extractor import PDFExtractor
import re

pdf_path = Path("C:/CODES/VQP/datapipeline/data/NCERT-Class-12-Physics-Part-1.pdf")
extractor = PDFExtractor()
res = extractor.extract_pdf(pdf_path)
pages = res["pages"]

print(f"Total pages: {len(pages)}")

chapters = [
    "Electric Charges and Fields",
    "Electrostatic Potential and Capacitance",
    "Current Electricity",
    "Moving Charges and Magnetism",
    "Magnetism and Matter",
    "Electromagnetic Induction",
    "Alternating Current",
    "Electromagnetic Waves"
]

# Let's search each page for chapter keywords and print matches
for idx, page in enumerate(pages):
    # Search for "CHAPTER" followed by word representation of numbers or actual numbers
    # e.g., CHAPTER ONE, CHAPTER TWO, CHAPTER 1, etc.
    chap_match = re.search(r"CHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|\d+)", page, re.IGNORECASE)
    if chap_match:
        print(f"Page {idx+1}: Found chap match: {chap_match.group(0)}")
        # Print surrounding text (100 chars)
        start = max(0, chap_match.start() - 20)
        end = min(len(page), chap_match.end() + 100)
        print("  Context:", repr(page[start:end]))
        
    for ch_name in chapters:
        # Search case insensitively
        if ch_name.lower() in page.lower():
            print(f"Page {idx+1}: Found Chapter Name '{ch_name}'")
            pos = page.lower().find(ch_name.lower())
            start = max(0, pos - 20)
            end = min(len(page), pos + len(ch_name) + 100)
            print("  Context:", repr(page[start:end]))
