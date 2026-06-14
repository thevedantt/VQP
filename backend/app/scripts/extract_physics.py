import os
import sys
from pathlib import Path

# Add the scripts directory and app directory to the system path to allow clean imports
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

try:
    from pdf_extractor import PDFExtractor, logger
except ImportError:
    # Fallback if run differently
    from .pdf_extractor import PDFExtractor, logger

def main():
    # Define directories relative to this script
    # Current script is at backend/app/scripts/extract_physics.py
    # Physics data is at backend/app/data/Physics/
    base_dir = current_dir.parent
    physics_dir = base_dir / "data" / "Physics"
    processed_dir = physics_dir / "processed"

    logger.info(f"Physics PDF directory: {physics_dir}")
    logger.info(f"Target processed directory: {processed_dir}")

    if not physics_dir.exists():
        logger.error(f"Physics data directory does not exist: {physics_dir}")
        sys.exit(1)

    # Find all PDF files in the directory
    pdf_files = sorted(list(physics_dir.glob("*.pdf")))
    if not pdf_files:
        logger.warning(f"No PDF files found in {physics_dir}")
        sys.exit(0)

    logger.info(f"Found {len(pdf_files)} PDF files to process.")

    # Initialize PDFExtractor
    extractor = PDFExtractor(fallback_to_pypdf=True)
    
    success_count = 0
    fail_count = 0

    print("\n" + "="*80)
    print("STARTING PDF EXTRACTION PIPELINE")
    print("="*80 + "\n")

    for pdf_file in pdf_files:
        result = extractor.extract_pdf(pdf_file, output_dir=processed_dir)
        
        if result["success"]:
            success_count += 1
            print(f"File Name: {result['file_name']}")
            print(f"Page Count: {result['page_count']}")
            print(f"Extracted Character Count: {result['char_count']}")
            print("-" * 40)
            print("First 500 characters preview:")
            print(result["preview"])
            print("-" * 80 + "\n")
        else:
            fail_count += 1
            print(f"File Name: {result['file_name']}")
            print(f"STATUS: FAILED")
            print(f"Error: {result['error']}")
            print("-" * 80 + "\n")

    print("="*80)
    print(f"EXTRACTION SUMMARY")
    print(f"Total PDFs found: {len(pdf_files)}")
    print(f"Successfully processed: {success_count}")
    print(f"Failed: {fail_count}")
    print("="*80)

if __name__ == "__main__":
    main()
