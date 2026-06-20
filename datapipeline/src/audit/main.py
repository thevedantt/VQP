import json
import sys
from pathlib import Path

# Ensure absolute import path works
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root / "src"))

from utils.logger import logger
from audit.sampler import MetadataSampler
from audit.validator import MetadataAuditValidator
from audit.statistics import MetadataStatistics
from audit.diagram_analysis import DiagramAnalysis

def main():
    # Define paths
    input_labeled_path = project_root.parent / "archive" / "backend" / "app" / "data" / "question_bank" / "labeled_questions.json"

    # Target files to output
    validation_sample_path = project_root.parent / "archive" / "backend" / "app" / "data" / "question_bank" / "validation_sample.json"
    review_dataset_path = project_root.parent / "archive" / "backend" / "app" / "data" / "question_bank" / "review_dataset.json"
    quality_flags_path = project_root.parent / "archive" / "backend" / "app" / "data" / "question_bank" / "quality_flags.json"
    diagram_analysis_path = project_root.parent / "archive" / "backend" / "app" / "data" / "question_bank" / "diagram_analysis.json"
    statistics_path = project_root.parent / "archive" / "backend" / "app" / "data" / "question_bank" / "dataset_statistics.json"

    # Make sure target dir exists
    input_labeled_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if input labeled data exists
    if not input_labeled_path.exists():
        logger.error(f"Labeled questions not found at {input_labeled_path}")
        sys.exit(1)

    # Load questions
    try:
        with open(input_labeled_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        sys.exit(1)

    # Instantiation
    sampler = MetadataSampler()
    audit_validator = MetadataAuditValidator()
    stats_calculator = MetadataStatistics()
    diag_analyzer = DiagramAnalysis()

    # Phase 1 & 2: Sampling and Review Formatting
    sample = sampler.sample_questions(questions, sample_size=20)
    review_set = sampler.generate_review_dataset(sample)

    with open(validation_sample_path, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=4)
    with open(review_dataset_path, "w", encoding="utf-8") as f:
        json.dump(review_set, f, indent=4)

    # Phase 3: Statistics
    stats = stats_calculator.calculate_stats(questions)
    with open(statistics_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)

    # Phase 4: Diagram Analysis
    diag_stats = diag_analyzer.analyze(questions)
    with open(diagram_analysis_path, "w", encoding="utf-8") as f:
        json.dump(diag_stats, f, indent=4)

    # Phase 5: Quality Flags
    flags = audit_validator.audit_quality(questions)
    with open(quality_flags_path, "w", encoding="utf-8") as f:
        json.dump(flags, f, indent=4)

    # Calculate audit-specific stats
    sample_diagram_count = sum(1 for q in sample if q.get("requires_diagram"))
    
    chapter_coverage = {}
    concept_coverage = {}
    for q in sample:
        ch = q.get("chapter", "Unknown")
        con = q.get("concept", "General")
        chapter_coverage[ch] = chapter_coverage.get(ch, 0) + 1
        concept_coverage[con] = concept_coverage.get(con, 0) + 1

    # 6. Terminal Report Output
    print("\n==================================================")
    print("METADATA AUDIT REPORT")
    print("=====================\n")
    print(f"Questions Audited: {len(sample)}")
    print(f"Potential Issues Found: {len(flags)}")
    print(f"Diagram Questions: {sample_diagram_count}\n")
    
    print("Chapter Coverage:")
    for ch, count in sorted(chapter_coverage.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ch}: {count}")
        
    print("\nConcept Coverage:")
    for con, count in sorted(concept_coverage.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {con}: {count}")

    print("\nRecommended Action:")
    if len(flags) < 10:
        print("Proceed to Diagram Detection")
    else:
        print("Review Labels")
    print("\n==================================================")

if __name__ == "__main__":
    main()
