import json
from pathlib import Path
from typing import List, Dict, Any
from utils.logger import logger
from question_extraction.models import QuestionModel, ExtractionReportModel

class QuestionValidator:
    """
    Validates extracted questions and generates the extraction reports.
    """

    def validate_and_generate_report(self, questions: List[QuestionModel], filename: str, reports_dir: Path) -> Dict[str, Any]:
        """
        Validates questions list, counts types, and saves extraction report.
        """
        reports_dir.mkdir(parents=True, exist_ok=True)

        mcqs = 0
        vsa = 0
        sa = 0
        case_study = 0
        la = 0

        for q in questions:
            # Basic validation
            if not q.question or len(q.question.strip()) == 0:
                logger.warning(f"Empty question text detected for Q{q.question_no} in {filename}")

            if q.type == "MCQ" or q.type == "Assertion Reason":
                mcqs += 1
                if not q.options or len(q.options) < 4:
                    logger.warning(f"MCQ Q{q.question_no} in {filename} has less than 4 options: {list(q.options.keys())}")
            elif q.type == "Very Short Answer (VSA)":
                vsa += 1
            elif q.type == "Short Answer (SA)":
                sa += 1
            elif q.type == "Case Study":
                case_study += 1
            elif q.type == "Long Answer (LA)":
                la += 1

        # Determine status
        status = "success" if len(questions) > 0 else "failed"

        report = ExtractionReportModel(
            file=filename,
            questions_found=len(questions),
            mcqs=mcqs,
            vsa=vsa,
            sa=sa,
            case_study=case_study,
            la=la,
            status=status
        )

        # Save report
        report_path = reports_dir / f"{Path(filename).stem}_extraction_report.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report.dict(), f, indent=4)
            logger.info(f"Saved extraction report to {report_path}")
        except Exception as e:
            logger.error(f"Failed to save extraction report for {filename}: {str(e)}")

        return report.dict()
