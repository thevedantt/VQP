from pathlib import Path
from typing import List, Dict, Any, Tuple

from utils.logger import logger
from labeling.lmstudio_client import LMStudioClient
from labeling.prompt_builder import PromptBuilder
from labeling.validator import LabelValidator

class LabelGenerator:
    """
    Manages the batch labeling of questions using local LM Studio.
    """

    def __init__(self, client: LMStudioClient):
        self.client = client
        self.prompt_builder = PromptBuilder()
        self.validator = LabelValidator()

    @staticmethod
    def is_corrupted(text: str) -> bool:
        """
        Determines if a question text is corrupted based on Private Use Area characters,
        replacement characters, and minimum length.
        """
        if not text or len(text.strip()) < 10:
            return True

        # Private Use Area ranges (e.g. \ue000-\uf8ff)
        pua_count = sum(1 for c in text if '\ue000' <= c <= '\uf8ff')
        
        # Replacement and control characters
        corrupt_count = sum(1 for c in text if c == '\ufffd' or (ord(c) < 32 and c not in '\n\r\t'))
        
        total_len = len(text)
        corrupt_ratio = (pua_count + corrupt_count) / total_len
        return corrupt_ratio > 0.30

    def generate_labels(self, questions: List[Dict[str, Any]], limit: int = 5) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Processes a limit subset of questions and generates metadata labels.
        Returns a tuple of (labeled_questions, stats_dict).
        """
        labeled_questions = []
        subset = questions[:limit]

        logger.info(f"Starting metadata labeling on {len(subset)} questions...")

        system_prompt = self.prompt_builder.build_system_prompt()
        
        success_count = 0
        failed_count = 0

        for idx, q in enumerate(subset):
            # Generate unique question_id
            src_clean = q.get("source_file", "unknown").replace(".txt", "").replace(".pdf", "")
            q_no = q.get("question_no", idx + 1)
            question_id = f"Q_{src_clean}_{q_no:02d}"

            logger.info(f"Labeling question {idx + 1}/{len(subset)}: {question_id}")

            user_prompt = self.prompt_builder.build_user_prompt(q)
            
            validated_data = None
            
            # Retry up to 3 times
            for attempt in range(1, 4):
                logger.info(f"Labeling Attempt {attempt} for {question_id}...")
                logger.info(f"Prompt Sent:\nSystem: {system_prompt[:200]}...\nUser: {user_prompt}")
                
                llm_res = self.client.call_llm(system_prompt, user_prompt, max_retries=1)
                logger.info(f"Raw Response received: {llm_res}")

                if llm_res:
                    validated_data = self.validator.validate_and_parse(llm_res)
                    logger.info(f"Parsed JSON outcome: {validated_data}")
                    if validated_data:
                        break
                
                logger.warning(f"Attempt {attempt} failed for {question_id}.")

            if validated_data:
                # Merge validated labels with original question metadata
                full_labeled = {
                    "question_id": question_id,
                    "source_file": q.get("source_file"),
                    "section": q.get("section"),
                    "type": q.get("type"),
                    "marks": q.get("marks"),
                    "chapter": validated_data["chapter"],
                    "concept": validated_data["concept"],
                    "difficulty": validated_data["difficulty"],
                    "question": q.get("question"),
                    "options": q.get("options", {}),
                    "requires_diagram": validated_data["requires_diagram"],
                    "diagram_type": validated_data["diagram_type"]
                }
                labeled_questions.append(full_labeled)
                success_count += 1
                logger.info(f"Successfully labeled {question_id}")
            else:
                failed_count += 1
                logger.error(f"Final failure for {question_id}. Skipping record.")

        stats = {
            "total_processed": len(subset),
            "successful_labels": success_count,
            "failed_labels": failed_count
        }

        return labeled_questions, stats

