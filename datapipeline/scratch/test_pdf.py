import sys
from pathlib import Path

# Ensure absolute import path works
src_root = Path(__file__).resolve().parents[1] / "src"
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from extraction.pdf_extractor import PDFExtractor

pdf_path = Path("C:/CODES/VQP/datapipeline/data/NCERT-Class-12-Physics-Part-1.pdf")
extractor = PDFExtractor()
res = extractor.extract_pdf(pdf_path)
print("SUCCESS:", res["success"])
print("PAGE COUNT:", res["page_count"])
pages = res["pages"]

# Print first 2000 chars of first 15 pages to understand layout
for idx in range(min(15, len(pages))):
    print(f"--- PAGE {idx+1} ---")
    print(pages[idx][:500])
