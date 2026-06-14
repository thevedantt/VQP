import json
import os
import sys
from pathlib import Path

# Ensure absolute import path works
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root / "src"))

from utils.logger import logger
from labeling.lmstudio_client import LMStudioClient
from labeling.prompt_builder import PromptBuilder
from labeling.validator import LabelValidator
from labeling.label_generator import LabelGenerator

def main():
    # Define paths
    input_dataset_path = project_root.parent / "backend" / "app" / "data" / "question_bank" / "final_dataset.json"
    output_labeled_path = project_root.parent / "backend" / "app" / "data" / "question_bank" / "labeled_questions.json"
    corrupted_out_path = project_root.parent / "backend" / "app" / "data" / "question_bank" / "corrupted_questions.json"
    
    reports_dir = project_root / "data" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_output_path = reports_dir / "labeling_report.json"
    backend_report_path = project_root.parent / "backend" / "app" / "data" / "question_bank" / "labeling_report.json"

    # Check if input file exists
    if not input_dataset_path.exists():
        logger.error(f"Input file not found at {input_dataset_path}")
        sys.exit(1)

    # Load questions
    try:
        with open(input_dataset_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
        total_questions = len(questions)
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        sys.exit(1)

    # Resume capability: Read already processed questions
    labeled_questions = []
    processed_ids = set()
    if output_labeled_path.exists():
        try:
            with open(output_labeled_path, "r", encoding="utf-8") as f:
                labeled_questions = json.load(f)
            processed_ids = {q["question_id"] for q in labeled_questions}
            logger.info(f"Resuming pipeline. Found {len(processed_ids)} already labeled questions.")
        except Exception as e:
            logger.error(f"Error reading existing labeled questions: {str(e)}")

    # Load corrupted questions to resume or initialize
    corrupted_questions = []
    corrupted_ids = set()
    if corrupted_out_path.exists():
        try:
            with open(corrupted_out_path, "r", encoding="utf-8") as f:
                corrupted_questions = json.load(f)
            corrupted_ids = {q["question_id"] for q in corrupted_questions}
            logger.info(f"Loaded {len(corrupted_ids)} already identified corrupted questions.")
        except Exception as e:
            logger.error(f"Error reading existing corrupted questions: {str(e)}")

    # Load failed/skipped questions to resume or initialize
    failed_questions = []
    failed_ids = set()

    # Initialize client and helper classes
    client = LMStudioClient()
    prompt_builder = PromptBuilder()
    validator = LabelValidator()
    system_prompt = prompt_builder.build_system_prompt()

    batch_size = 10
    current_batch_labeled = []
    
    # Filter questions that are not processed or corrupted
    questions_to_process = []
    for idx, q in enumerate(questions):
        src_clean = q.get("source_file", "unknown").replace(".txt", "").replace(".pdf", "")
        q_no = q.get("question_no", idx + 1)
        question_id = f"Q_{src_clean}_{q_no:02d}"
        
        # Attach question_id to q for convenience
        q_copy = dict(q)
        q_copy["question_id"] = question_id
        
        if question_id in processed_ids or question_id in corrupted_ids:
            continue
            
        questions_to_process.append(q_copy)

    logger.info(f"Total questions to label in this run: {len(questions_to_process)}")

    processed_count_in_run = len(processed_ids) + len(corrupted_ids)
    
    # Process in batches
    for i in range(0, len(questions_to_process), batch_size):
        batch_slice = questions_to_process[i:i + batch_size]
        batch_num = (processed_count_in_run // batch_size) + 1
        
        batch_labeled = []
        batch_corrupted = []
        batch_failed = []

        for q in batch_slice:
            question_id = q["question_id"]
            question_text = q.get("question", "")

            # 3. Corrupted Question Detection
            if LabelGenerator.is_corrupted(question_text):
                logger.warning(f"Corrupted question detected: {question_id}")
                batch_corrupted.append(q)
                continue

            # Submit to LLM with retry up to 3 times
            user_prompt = prompt_builder.build_user_prompt(q)
            validated_data = None
            
            for attempt in range(1, 4):
                llm_res = client.call_llm(system_prompt, user_prompt, max_retries=1)
                if llm_res:
                    validated_data = validator.validate_and_parse(llm_res)
                    if validated_data:
                        break
                logger.warning(f"Attempt {attempt} failed for {question_id}.")

            if validated_data:
                full_labeled = {
                    "question_id": question_id,
                    "source_file": q.get("source_file"),
                    "section": q.get("section"),
                    "type": q.get("type"),
                    "marks": q.get("marks"),
                    "chapter": validated_data["chapter"],
                    "concept": validated_data["concept"],
                    "difficulty": validated_data["difficulty"],
                    "question": question_text,
                    "options": q.get("options", {}),
                    "requires_diagram": validated_data["requires_diagram"],
                    "diagram_type": validated_data["diagram_type"]
                }
                batch_labeled.append(full_labeled)
            else:
                logger.error(f"Final failure for {question_id}. Skipping.")
                batch_failed.append(q)

        # Update cumulative lists
        labeled_questions.extend(batch_labeled)
        corrupted_questions.extend(batch_corrupted)
        failed_questions.extend(batch_failed)
        
        # Update processed ID sets
        for q in batch_labeled:
            processed_ids.add(q["question_id"])
        for q in batch_corrupted:
            corrupted_ids.add(q["question_id"])
        for q in batch_failed:
            failed_ids.add(q["question_id"])

        processed_count_in_run += len(batch_slice)

        # 6. Save Incrementally after every batch
        try:
            with open(output_labeled_path, "w", encoding="utf-8") as f:
                json.dump(labeled_questions, f, indent=4)
            with open(corrupted_out_path, "w", encoding="utf-8") as f:
                json.dump(corrupted_questions, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving incremental batch progress: {str(e)}")

        # 5. Progress Logging
        diagram_detected_in_batch = sum(1 for q in batch_labeled if q.get("requires_diagram"))
        print(f"\n---")
        print(f"Batch: {batch_num}")
        print(f"Processed: {processed_count_in_run} / {total_questions}")
        print(f"Successful: {len(batch_labeled)}")
        print(f"Skipped Corrupted: {len(batch_corrupted)}")
        print(f"Diagram Questions: {diagram_detected_in_batch}")
        print(f"--------------------\n")

    # Generate final stats
    diagram_total = sum(1 for q in labeled_questions if q.get("requires_diagram"))
    
    chapter_dist = {}
    concept_dist = {}
    for q in labeled_questions:
        chapter = q.get("chapter", "Unknown")
        concept = q.get("concept", "General")
        chapter_dist[chapter] = chapter_dist.get(chapter, 0) + 1
        concept_dist[concept] = concept_dist.get(concept, 0) + 1

    # 7. Final Report
    report = {
        "total_questions": total_questions,
        "processed": len(processed_ids) + len(failed_ids),
        "successful_labels": len(labeled_questions),
        "corrupted_questions": len(corrupted_questions),
        "failed_questions": len(failed_questions),
        "diagram_questions_detected": diagram_total,
        "chapter_distribution": chapter_dist,
        "concept_distribution": concept_dist
    }

    try:
        with open(report_output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        with open(backend_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save final report: {str(e)}")

    # 8. Terminal Summary
    print("\n==================================================")
    print("AI LABELING COMPLETE")
    print("====================\n")
    print(f"Total Questions: {total_questions}")
    print(f"Successfully Labeled: {len(labeled_questions)}")
    print(f"Corrupted Questions Skipped: {len(corrupted_questions)}")
    print(f"Failed Questions: {len(failed_questions)}")
    print(f"\nDiagram Questions Detected: {diagram_total}\n")
    print("Chapter Distribution:")
    for ch, count in sorted(chapter_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ch}: {count}")
    print("\nConcept Distribution:")
    for con, count in sorted(concept_dist.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {con}: {count}")
    print(f"\nOutput Saved:")
    print(f"  {output_labeled_path}")
    print("\n==================================================")

if __name__ == "__main__":
    main()
