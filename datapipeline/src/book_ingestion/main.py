import sys
from pathlib import Path

# Ensure absolute import path works
src_root = Path(__file__).resolve().parents[1]
if str(src_root) not in sys.path:
    sys.path.append(str(src_root))

from book_ingestion.extractor import BookExtractor
from book_ingestion.cleaner import BookCleaner
from book_ingestion.chapter_detector import ChapterDetector
from book_ingestion.chapter_splitter import ChapterSplitter
from book_ingestion.exporter import Exporter
from book_ingestion.statistics import BookStatistics
from utils.logger import logger

def run_pipeline(pdf_path: Path, output_dir: Path) -> None:
    """
    Runs the end-to-end NCERT Physics Book Ingestion Pipeline.
    """
    logger.info("Starting NCERT Physics Ingestion Pipeline...")
    
    # Phase 1: Extraction
    extractor = BookExtractor()
    extraction_result = extractor.extract(pdf_path)
    if not extraction_result.get("success"):
        logger.error(f"Extraction failed: {extraction_result.get('error')}")
        sys.exit(1)
    
    raw_pages = extraction_result["pages"]
    total_pages = extraction_result["page_count"]
    logger.info(f"Extracted {total_pages} pages from PDF.")

    # Phase 2: Cleaning
    cleaner = BookCleaner()
    cleaned_pages = cleaner.clean_pages(raw_pages)
    logger.info("Pages cleaned successfully.")

    # Phase 3: Chapter Detection
    detector = ChapterDetector()
    detected_chapters = detector.detect(cleaned_pages)
    logger.info(f"Detected {len(detected_chapters)} chapters.")

    if not detected_chapters:
        logger.error("No chapters detected! Aborting pipeline.")
        sys.exit(1)

    # Phase 4: Chapter Splitting
    splitter = ChapterSplitter()
    chapters_content = splitter.split(cleaned_pages, detected_chapters)

    # Phase 5, 6, 7: Exporting (Knowledge Base, Chapter files, and Chapter Index)
    exporter = Exporter(output_dir)
    exporter.export(chapters_content)

    # Phase 8: Statistics Generation
    statistics = BookStatistics(output_dir)
    stats = statistics.generate(chapters_content, total_pages_processed=total_pages)

    # Phase 9: Terminal Report
    total_words = stats["total_words"]
    print("\n" + "=" * 50)
    print("NCERT BOOK INGESTION COMPLETE")
    print("=" * 29)
    print(f"\nBook:\nNCERT Physics Class 12 Part 1\n")
    print(f"Pages Processed: {total_pages}\n")
    print(f"Chapters Extracted: {len(chapters_content)}\n")
    print(f"Total Words: {total_words}\n")
    print("Generated Files:\n")
    print(" * physics_part1_knowledge_base.json")
    print(" * chapter_index.json")
    print(" * book_statistics.json")
    print(" * chapter files\n")
    print("Output Location:\n")
    print(f"{output_dir.as_posix()}\n")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    # Define absolute input and output paths
    DEFAULT_PDF_PATH = Path("C:/CODES/VQP/datapipeline/data/NCERT-Class-12-Physics-Part-1.pdf")
    DEFAULT_OUTPUT_DIR = Path("C:/CODES/VQP/backend/app/data/Book/")
    
    run_pipeline(DEFAULT_PDF_PATH, DEFAULT_OUTPUT_DIR)
