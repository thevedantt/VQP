import os
import sys
import logging
from pathlib import Path

# Add scripts directory to path to allow direct imports
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("QualityAnalyzer")

try:
    from metrics import analyze_text_metrics
    from report_generator import save_individual_report, generate_and_save_summary, print_terminal_report
except ImportError:
    from .metrics import analyze_text_metrics
    from .report_generator import save_individual_report, generate_and_save_summary, print_terminal_report

def main():
    # Define directories relative to this script
    # Current script is at backend/app/scripts/quality_analyzer.py
    # Physics processed data is at backend/app/data/Physics/processed/
    # Reports should go to backend/app/data/Physics/reports/
    base_dir = current_dir.parent
    physics_dir = base_dir / "data" / "Physics"
    processed_dir = physics_dir / "processed"
    reports_dir = physics_dir / "reports"

    logger.info("Starting Dataset Quality Analysis...")
    logger.info(f"Source directory: {processed_dir}")
    logger.info(f"Reports directory: {reports_dir}")

    if not processed_dir.exists():
        logger.error(f"Processed directory does not exist: {processed_dir}")
        sys.exit(1)

    # Get all .txt files
    txt_files = sorted(list(processed_dir.glob("*.txt")))
    if not txt_files:
        logger.warning(f"No processed .txt files found in {processed_dir}")
        sys.exit(0)

    logger.info(f"Found {len(txt_files)} text files to analyze.")

    all_reports = []
    
    for txt_file in txt_files:
        try:
            logger.info(f"Analyzing {txt_file.name}...")
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()

            # Run metrics analysis
            metrics = analyze_text_metrics(text)
            metrics["file_name"] = txt_file.name
            
            # Save individual report
            save_individual_report(txt_file.name, metrics, reports_dir)
            all_reports.append(metrics)
            
        except Exception as e:
            logger.error(f"Failed to analyze {txt_file.name}: {str(e)}")
            # Add a stub report to indicate failure
            stub_report = {
                "file_name": txt_file.name,
                "success": False,
                "readability_score": 0,
                "reliability_score": 0,
                "status": "Poor",
                "issues": [f"Analysis failed: {str(e)}"]
            }
            save_individual_report(txt_file.name, stub_report, reports_dir)
            all_reports.append(stub_report)

    # Generate master report and save
    summary = generate_and_save_summary(all_reports, reports_dir)

    # Print requested terminal output format
    print_terminal_report(all_reports, summary)

if __name__ == "__main__":
    main()
