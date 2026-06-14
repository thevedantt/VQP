import json
from pathlib import Path
from typing import List, Dict, Any

from utils.logger import logger

class QuestionDataValidator:
    """
    Validates question records against core schema rules and filters malformed ones.
    """

    def validate_dataset(self, questions: List[Dict[str, Any]], reports_dir: Path) -> List[Dict[str, Any]]:
        """
        Validates all questions in the list, generates validation_report.json,
        and returns the list of valid questions.
        """
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        valid_questions = []
        malformed_records = []
        errors = []

        for idx, q in enumerate(questions):
            q_no = q.get("question_no", idx + 1)
            source = q.get("source_file", "unknown")
            record_id = f"Q{q_no} from {source}"
            
            # Validation checks
            issue_found = False
            reasons = []

            # 1. Question text exists
            q_text = q.get("question")
            if not q_text or not str(q_text).strip():
                issue_found = True
                reasons.append("Missing question text")

            # 2. Section exists
            sect = q.get("section")
            if not sect or not str(sect).strip():
                issue_found = True
                reasons.append("Missing section")

            # 3. Type exists
            q_type = q.get("type")
            if not q_type or not str(q_type).strip():
                issue_found = True
                reasons.append("Missing question type")

            # 4. Marks exists
            marks = q.get("marks")
            if marks is None or not isinstance(marks, int):
                issue_found = True
                reasons.append("Missing or invalid marks")

            # 5. MCQ options check
            if q_type == "MCQ":
                opts = q.get("options", {})
                if not isinstance(opts, dict) or len(opts) < 4:
                    issue_found = True
                    reasons.append(f"MCQ has less than 4 options: {list(opts.keys()) if isinstance(opts, dict) else 'not a dict'}")
                else:
                    # Verify A, B, C, D exist and are not empty
                    for key in ["A", "B", "C", "D"]:
                        if key not in opts or not str(opts[key]).strip():
                            issue_found = True
                            reasons.append(f"MCQ missing option {key}")

            if issue_found:
                malformed_records.append({
                    "record_id": record_id,
                    "reasons": reasons,
                    "record_data": q
                })
                errors.append(f"Record {record_id} is malformed: {', '.join(reasons)}")
                logger.warning(f"Malformed record: {record_id} - {reasons}")
            else:
                valid_questions.append(q)

        # Generate validation report
        report = {
            "total_records_checked": len(questions),
            "valid_records": len(valid_questions),
            "malformed_records_count": len(malformed_records),
            "malformed_records": malformed_records
        }

        report_path = reports_dir / "validation_report.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4)
            logger.info(f"Saved dataset validation report to {report_path}")
        except Exception as e:
            logger.error(f"Failed to save validation report: {str(e)}")

        return valid_questions
