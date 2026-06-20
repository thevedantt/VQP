import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Ensure absolute import path works
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root / "src"))

from utils.logger import logger
from extraction.pdf_extractor import PDFExtractor
from cleaning.text_cleaner import TextCleaner
from validation.quality_validator import QualityValidator
from question_extraction.extractor import QuestionExtractor
from question_extraction.validator import QuestionValidator

# Integration of Prep & Validation modules
from validation.validator import QuestionDataValidator
from validation.deduplicator import QuestionDeduplicator
from validation.statistics import DatasetStatistics
from validation.exporter import FinalDatasetExporter

def main():
    # Define directories relative to project root
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw_pdfs"
    extracted_dir = data_dir / "extracted_text"
    cleaned_dir = data_dir / "cleaned_text"
    questions_dir = data_dir / "questions"
    reports_dir = data_dir / "reports"
    
    # Backend Export Directory
    backend_export_dir = project_root.parent / "archive" / "backend" / "app" / "data" / "question_bank"

    # Make sure target dirs exist
    extracted_dir.mkdir(parents=True, exist_ok=True)
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    questions_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    backend_export_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting STANDALONE DATA INGESTION AND PREPROCESSING PIPELINE")
    
    # Gather PDFs
    pdf_paths = sorted(list(raw_dir.glob("*.pdf")))
    if not pdf_paths:
        logger.warning(f"No PDFs found in {raw_dir}")
        return

    logger.info(f"Found {len(pdf_paths)} PDFs to process.")

    # Initialize Ingestion modules
    extractor = PDFExtractor(fallback_to_pypdf=True)
    cleaner = TextCleaner()
    validator = QualityValidator()

    # Preprocessing loop
    for pdf_path in pdf_paths:
        logger.info("-" * 60)
        logger.info(f"Ingesting: {pdf_path.name}")
        
        # Phase 1: Extraction
        extract_res = extractor.extract_pdf(pdf_path, output_dir=extracted_dir)
        if not extract_res["success"]:
            logger.error(f"Failed to extract {pdf_path.name}")
            continue

        # Phase 2: Cleaning
        cleaned_text = ""
        if extract_res["pages"]:
            cleaned_text = cleaner.clean_document_pages(extract_res["pages"])
        else:
            cleaned_text = cleaner.clean_document_text(extract_res["text"])

        # Phase 4: Save cleaned .txt
        txt_filename = pdf_path.stem + ".txt"
        clean_file_path = cleaned_dir / txt_filename
        try:
            with open(clean_file_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
            logger.info(f"Saved cleaned text to {clean_file_path}")
        except Exception as e:
            logger.error(f"Failed to save clean text for {pdf_path.name}: {str(e)}")

        # Phase 3: Validation report
        validator.validate(cleaned_text, pdf_path.name, reports_dir)

    logger.info("=" * 60)
    logger.info("Starting QUESTION EXTRACTION PIPELINE")
    logger.info(f"Input Directory (Cleaned Text): {cleaned_dir}")
    logger.info(f"Output Directory (JSON Questions): {questions_dir}")

    # Gather cleaned texts
    clean_txt_paths = sorted(list(cleaned_dir.glob("*.txt")))
    
    q_extractor = QuestionExtractor()
    q_validator = QuestionValidator()

    all_questions_master = []
    extraction_reports = []

    for txt_path in clean_txt_paths:
        logger.info("-" * 60)
        logger.info(f"Extracting questions from: {txt_path.name}")
        
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            
            # Extract questions
            questions = q_extractor.extract_questions(text_content, txt_path.name)
            
            # Save individual paper JSON (Phase 5 - 1)
            json_filename = txt_path.stem + ".json"
            json_out_path = questions_dir / json_filename
            questions_serialized = [q.dict() for q in questions]
            
            with open(json_out_path, "w", encoding="utf-8") as f:
                json.dump(questions_serialized, f, indent=4)
            logger.info(f"Saved {len(questions)} questions to {json_out_path}")
            
            # Accumulate master dataset (Phase 5 - 2)
            all_questions_master.extend(questions_serialized)
            
            # Validate and generate extraction report (Phase 6)
            report = q_validator.validate_and_generate_report(questions, txt_path.name, reports_dir)
            extraction_reports.append(report)
            
        except Exception as e:
            logger.error(f"Failed to extract questions from {txt_path.name}: {str(e)}", exc_info=True)

    # Save Master Question Bank
    master_bank_path = questions_dir / "master_question_bank.json"
    try:
        with open(master_bank_path, "w", encoding="utf-8") as f:
            json.dump(all_questions_master, f, indent=4)
        logger.info(f"Saved master question bank ({len(all_questions_master)} total questions) to {master_bank_path}")
    except Exception as e:
        logger.error(f"Failed to save master question bank: {str(e)}")

    logger.info("=" * 60)
    logger.info("Starting QUESTION VALIDATION AND DATASET PREPARATION PIPELINE")

    # Initialize prep modules
    dataset_validator = QuestionDataValidator()
    deduplicator = QuestionDeduplicator()
    stats_generator = DatasetStatistics()
    exporter = FinalDatasetExporter()

    # 1. Validation
    logger.info("Validating dataset...")
    valid_questions = dataset_validator.validate_dataset(all_questions_master, reports_dir)

    # 2. Deduplication
    logger.info("Deduplicating questions...")
    unique_questions = deduplicator.deduplicate(valid_questions, reports_dir, questions_dir)

    # 3. Statistics
    logger.info("Generating statistics...")
    final_stats = stats_generator.generate_statistics(len(all_questions_master), unique_questions, reports_dir)

    # 4. Backend Export
    logger.info("Exporting to backend data folder...")
    final_export_path = exporter.export(unique_questions, backend_export_dir)

    # Print summary of the runs
    print("\n" + "=" * 80)
    print(f"{'DATASET VALIDATION & DEDUPLICATION SUMMARY':^80}")
    print("=" * 80)
    print(f"Total Raw Extracted Questions : {len(all_questions_master)}")
    print(f"Malformed Records Removed     : {len(all_questions_master) - len(valid_questions)}")
    print(f"Duplicate Questions Removed   : {len(valid_questions) - len(unique_questions)}")
    print(f"Final Unique Questions        : {len(unique_questions)}")
    print(f"Exported Path                 : {final_export_path}")
    print("-" * 80)
    print("Questions by Section:")
    for sect, count in sorted(final_stats["questions_by_section"].items()):
        print(f"  Section {sect}: {count}")
    print("Questions by Type:")
    for q_type, count in sorted(final_stats["questions_by_type"].items()):
        print(f"  {q_type}: {count}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
