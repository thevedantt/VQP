import json
import sys
from pathlib import Path

# Ensure absolute import path works
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root / "src"))

from utils.logger import logger
from diagram_intelligence.lmstudio_client import LMStudioClient
from diagram_intelligence.prompt_builder import PromptBuilder
from diagram_intelligence.parser import DiagramResponseParser

def main():
    # Define paths
    input_labeled_path = project_root.parent / "backend" / "app" / "data" / "question_bank" / "labeled_questions.json"
    output_dataset_path = project_root.parent / "backend" / "app" / "data" / "question_bank" / "diagram_dataset.json"
    statistics_path = project_root.parent / "backend" / "app" / "data" / "question_bank" / "diagram_statistics.json"

    # Check input file
    if not input_labeled_path.exists():
        logger.error(f"Input file not found at {input_labeled_path}")
        sys.exit(1)

    # Load questions
    try:
        with open(input_labeled_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
        total_questions = len(questions)
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        sys.exit(1)

    # Resume capability: Read already processed questions
    diagram_dataset = []
    processed_ids = set()
    if output_dataset_path.exists():
        try:
            with open(output_dataset_path, "r", encoding="utf-8") as f:
                diagram_dataset = json.load(f)
            processed_ids = {q["question_id"] for q in diagram_dataset}
            logger.info(f"Resuming diagram intelligence. Found {len(processed_ids)} already processed questions.")
        except Exception as e:
            logger.error(f"Error reading existing diagram dataset: {str(e)}")

    # Initialize modules
    client = LMStudioClient()
    prompt_builder = PromptBuilder()
    response_parser = DiagramResponseParser()
    system_prompt = prompt_builder.build_system_prompt()

    batch_size = 10
    
    # Filter questions to process
    questions_to_process = [q for q in questions if q.get("question_id") not in processed_ids]
    logger.info(f"Total questions to process in this run: {len(questions_to_process)}")

    processed_count = len(processed_ids)

    for i in range(0, len(questions_to_process), batch_size):
        batch_slice = questions_to_process[i:i + batch_size]
        batch_labeled = []

        for q in batch_slice:
            question_id = q.get("question_id")
            question_text = q.get("question", "")
            
            logger.info(f"Processing diagram intelligence for {question_id}...")

            user_prompt = prompt_builder.build_user_prompt(q)
            validated_data = None
            
            # Retry up to 3 times if validation fails
            for attempt in range(1, 4):
                llm_res = client.call_llm(system_prompt, user_prompt)
                if llm_res:
                    validated_data = response_parser.parse_and_validate(llm_res)
                    if validated_data:
                        break
                logger.warning(f"Attempt {attempt} failed to return valid JSON for {question_id}.")

            if not validated_data:
                logger.warning(f"Failed to get LLM response for {question_id}. Using safe fallback.")
                # Fallback
                q_text_lower = question_text.lower()
                requires_diag = any(kw in q_text_lower for kw in ["draw", "sketch", "graph", "plot", "construct"])
                
                dtype = "none"
                if requires_diag:
                    if "circuit" in q_text_lower:
                        dtype = "circuit"
                    elif "graph" in q_text_lower or "plot" in q_text_lower:
                        dtype = "graph"
                    elif "ray" in q_text_lower or "lens" in q_text_lower or "mirror" in q_text_lower:
                        dtype = "ray_diagram"
                    else:
                        dtype = "graph"

                validated_data = {
                    "requires_diagram": requires_diag,
                    "diagram_type": dtype,
                    "confidence": 0.50,
                    "reason": "Fallback applied due to LLM response failure"
                }

            # Save re-evaluated diagram record
            record = {
                "question_id": question_id,
                "question": question_text,
                "requires_diagram": validated_data["requires_diagram"],
                "diagram_type": validated_data["diagram_type"],
                "confidence": validated_data["confidence"],
                "reason": validated_data["reason"]
            }
            batch_labeled.append(record)

        # Append and save batch incrementally
        diagram_dataset.extend(batch_labeled)
        processed_count += len(batch_slice)

        try:
            with open(output_dataset_path, "w", encoding="utf-8") as f:
                json.dump(diagram_dataset, f, indent=4)
            logger.info(f"Incremental progress saved. Processed: {processed_count}/{total_questions}")
        except Exception as e:
            logger.error(f"Failed to save incremental batch: {str(e)}")

    # Calculate final statistics
    diagram_questions = sum(1 for q in diagram_dataset if q.get("requires_diagram"))
    non_diagram_questions = total_questions - diagram_questions
    
    types_count = {
        "free_body": 0,
        "circuit": 0,
        "graph": 0,
        "ray_diagram": 0,
        "optical_instrument": 0,
        "magnetic_field": 0
    }
    
    total_confidence = 0.0
    for q in diagram_dataset:
        dtype = q.get("diagram_type", "none")
        if dtype in types_count:
            types_count[dtype] += 1
        total_confidence += q.get("confidence", 0.0)

    avg_confidence = total_confidence / max(1, total_questions)

    # Output stats file
    stats_data = {
        "total_questions": total_questions,
        "diagram_questions": diagram_questions,
        "non_diagram_questions": non_diagram_questions,
        "free_body": types_count["free_body"],
        "circuit": types_count["circuit"],
        "graph": types_count["graph"],
        "ray_diagram": types_count["ray_diagram"],
        "optical_instrument": types_count["optical_instrument"],
        "magnetic_field": types_count["magnetic_field"]
    }

    try:
        with open(statistics_path, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=4)
        logger.info(f"Saved diagram statistics to {statistics_path}")
    except Exception as e:
        logger.error(f"Failed to save statistics: {str(e)}")

    # Print terminal summary report
    print("\n==================================================")
    print("DIAGRAM INTELLIGENCE REPORT")
    print("===========================\n")
    print(f"Total Questions: {total_questions}")
    print(f"Diagram Questions: {diagram_questions}")
    print(f"Non Diagram Questions: {non_diagram_questions}\n")
    print("Diagram Types:\n")
    print(f"Free Body: {types_count['free_body']}")
    print(f"Circuit: {types_count['circuit']}")
    print(f"Graph: {types_count['graph']}")
    print(f"Ray Diagram: {types_count['ray_diagram']}")
    print(f"Optical Instrument: {types_count['optical_instrument']}")
    print(f"Magnetic Field: {types_count['magnetic_field']}\n")
    print(f"Average Confidence: {avg_confidence:.4f}\n")
    print("Output Saved:")
    print(f"  {output_dataset_path}")
    print("\n==================================================")

if __name__ == "__main__":
    main()
