import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PDFExtractor")

class PDFExtractor:
    """
    A modular utility to extract text from PDF files using PyMuPDF (fitz)
    with a fallback to PyPDF if PyMuPDF is not installed or fails.
    """

    def __init__(self, fallback_to_pypdf: bool = True):
        self.fallback_to_pypdf = fallback_to_pypdf
        self._check_libraries()

    def _check_libraries(self):
        # Check PyMuPDF availability
        try:
            import fitz  # PyMuPDF
            self.has_pymupdf = True
            logger.debug("PyMuPDF (fitz) is available and will be used as the primary extractor.")
        except ImportError:
            self.has_pymupdf = False
            logger.warning("PyMuPDF (fitz) is not installed. Will attempt PyPDF fallback if enabled.")

        # Check PyPDF availability
        try:
            import pypdf
            self.has_pypdf = True
            logger.debug("PyPDF is available for fallback.")
        except ImportError:
            self.has_pypdf = False
            logger.warning("PyPDF is not installed.")

    def extract_text_pymupdf(self, pdf_path: Path) -> tuple[str, int]:
        """Extracts text and page count using PyMuPDF (fitz)."""
        import fitz
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        text_list = []
        for page in doc:
            text_list.append(page.get_text())
        doc.close()
        return "\n".join(text_list), page_count

    def extract_text_pypdf(self, pdf_path: Path) -> tuple[str, int]:
        """Extracts text and page count using PyPDF."""
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        page_count = len(reader.pages)
        text_list = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_list.append(text)
        return "\n".join(text_list), page_count

    def extract_pdf(self, pdf_path: Path, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Extracts text from a single PDF file and optionally saves it.
        
        Args:
            pdf_path: Path to the input PDF file.
            output_dir: Optional directory to save the extracted .txt file.
            
        Returns:
            Dict containing extraction metadata and preview.
        """
        pdf_path = Path(pdf_path)
        result = {
            "file_name": pdf_path.name,
            "success": False,
            "page_count": 0,
            "char_count": 0,
            "preview": "",
            "error": None
        }

        if not pdf_path.exists():
            err_msg = f"File not found: {pdf_path}"
            logger.error(err_msg)
            result["error"] = err_msg
            return result

        logger.info(f"Starting extraction for: {pdf_path.name}")
        extracted_text = ""
        page_count = 0

        # Try PyMuPDF first
        if self.has_pymupdf:
            try:
                extracted_text, page_count = self.extract_text_pymupdf(pdf_path)
                result["success"] = True
                logger.info(f"Successfully extracted {pdf_path.name} using PyMuPDF.")
            except Exception as e:
                logger.error(f"PyMuPDF extraction failed for {pdf_path.name}: {str(e)}")
                if not self.fallback_to_pypdf:
                    result["error"] = f"PyMuPDF failed: {str(e)}"
                    return result

        # Fallback to PyPDF
        if not result["success"] and self.fallback_to_pypdf and self.has_pypdf:
            try:
                logger.info(f"Attempting PyPDF fallback for {pdf_path.name}...")
                extracted_text, page_count = self.extract_text_pypdf(pdf_path)
                result["success"] = True
                logger.info(f"Successfully extracted {pdf_path.name} using PyPDF.")
            except Exception as e:
                err_msg = f"Both PyMuPDF and PyPDF failed for {pdf_path.name}. Error: {str(e)}"
                logger.error(err_msg)
                result["error"] = err_msg
                return result
        elif not result["success"]:
            err_msg = f"Extraction failed for {pdf_path.name}. No suitable PDF library was successful."
            logger.error(err_msg)
            result["error"] = err_msg
            return result

        # Fill metadata
        result["page_count"] = page_count
        result["char_count"] = len(extracted_text)
        result["preview"] = extracted_text[:500]

        # Save to output folder if specified
        if output_dir:
            try:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                txt_filename = pdf_path.stem + ".txt"
                output_path = output_dir / txt_filename
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                
                logger.info(f"Saved extracted text to {output_path}")
            except Exception as e:
                logger.error(f"Failed to save extracted text for {pdf_path.name}: {str(e)}")
                # We don't mark success as False because text was successfully extracted,
                # but we record the saving error.
                result["error"] = f"Failed to save file: {str(e)}"

        return result
