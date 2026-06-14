import sys
from pathlib import Path
from typing import Dict, Any

# Ensure absolute import path works
src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from extraction.pdf_extractor import PDFExtractor
from utils.logger import logger

class BookExtractor:
    """
    Wrapper around PDFExtractor to extract text and pages for book ingestion.
    """
    def __init__(self) -> None:
        self.extractor = PDFExtractor(fallback_to_pypdf=True)

    def extract(self, pdf_path: Path) -> Dict[str, Any]:
        logger.info(f"Extracting PDF content from: {pdf_path}")
        result = self.extractor.extract_pdf(pdf_path)
        return result
