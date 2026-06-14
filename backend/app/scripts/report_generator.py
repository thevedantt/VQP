import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("ReportGenerator")

def save_individual_report(filename: str, metrics: Dict[str, Any], reports_dir: Path) -> Path:
    """Saves the metrics for a single file as a JSON report."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_name = filename.replace(".txt", "_report.json")
    if not report_name.endswith("_report.json"):
        report_name = f"{filename}_report.json"
        
    report_path = reports_dir / report_name
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
        
    logger.debug(f"Saved individual report to {report_path}")
    return report_path

def generate_and_save_summary(all_reports: List[Dict[str, Any]], reports_dir: Path) -> Dict[str, Any]:
    """
    Computes overall summary statistics, writes the master JSON report,
    and returns the summary data.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path = reports_dir / "dataset_summary.json"
    
    total_files = len(all_reports)
    if total_files == 0:
        summary = {
            "total_files": 0,
            "overall_quality_score": 0,
            "status_counts": {"Excellent": 0, "Good": 0, "Needs Cleaning": 0, "Poor": 0},
            "files": []
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4)
        return summary

    # Count statuses
    status_counts = {"Excellent": 0, "Good": 0, "Needs Cleaning": 0, "Poor": 0}
    total_reliability = 0.0
    
    for report in all_reports:
        status = report.get("status", "Poor")
        status_counts[status] = status_counts.get(status, 0) + 1
        total_reliability += report.get("reliability_score", 0)
        
    overall_quality = int(round(total_reliability / total_files))
    
    summary = {
        "total_files": total_files,
        "overall_quality_score": overall_quality,
        "status_counts": status_counts,
        "files": all_reports
    }
    
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
        
    logger.info(f"Saved master report to {summary_path}")
    return summary

def print_terminal_report(all_reports: List[Dict[str, Any]], summary: Dict[str, Any]):
    """Prints the final summary report to the terminal in the exact required format."""
    print("\n" + "="*50)
    print("DATASET QUALITY REPORT")
    print("="*22 + "\n")
    
    for report in all_reports:
        print(f"File: {report['file_name']}")
        print(f"Readability Score: {report['readability_score']}")
        print(f"Reliability Score: {report['reliability_score']}")
        print(f"Status: {report['status']}")
        if report.get("issues"):
            print(f"Issues: {', '.join(report['issues'])}")
        print("\n---" + "\n")
        
    print(f"Overall Dataset Quality: {summary['overall_quality_score']}")
    print(f"Excellent Files: {summary['status_counts']['Excellent']}")
    print(f"Good Files: {summary['status_counts']['Good']}")
    print(f"Needs Cleaning: {summary['status_counts']['Needs Cleaning']}")
    print(f"Poor Files: {summary['status_counts']['Poor']}")
    
    # Recommendation logic
    overall_quality = summary['overall_quality_score']
    poor_files = summary['status_counts']['Poor']
    needs_cleaning_files = summary['status_counts']['Needs Cleaning']
    
    print("\nRecommended Action:")
    if overall_quality >= 80 and poor_files == 0:
        print("Proceed to Question Extraction")
    elif overall_quality >= 60 and (poor_files > 0 or needs_cleaning_files > 0):
        print("Clean files with 'Needs Cleaning' and 'Poor' statuses before extraction")
    else:
        print("Re-run extraction pipeline or perform significant manual cleanup")
        
    print("\n" + "="*50)
