import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logger import logger
from question_extraction.models import QuestionModel
from question_extraction.parser import QuestionParser

class QuestionExtractor:
    """
    Extracts questions from cleaned CBSE Physics text files into structured models.
    """

    def __init__(self):
        self.parser = QuestionParser()
        self.section_pattern = re.compile(r"^\s*SECTION\s+([A-E])\s*$", re.IGNORECASE)
        self.question_start_pattern = re.compile(r"^\s*(\d+)\.\s*$")

    def get_section_from_no(self, q_no: int) -> str:
        """Fallback to infer section from question number if header is missing."""
        if 1 <= q_no <= 16:
            return "A"
        elif 17 <= q_no <= 21:
            return "B"
        elif 22 <= q_no <= 28:
            return "C"
        elif 29 <= q_no <= 30:
            return "D"
        elif 31 <= q_no <= 33:
            return "E"
        return "Unknown"

    def get_type_and_marks(self, q_no: int, section: str) -> tuple[str, int]:
        """Determines question type and marks from the question number and section."""
        if section == "A":
            if 13 <= q_no <= 16:
                return "Assertion Reason", 1
            return "MCQ", 1
        elif section == "B":
            return "Very Short Answer (VSA)", 2
        elif section == "C":
            return "Short Answer (SA)", 3
        elif section == "D":
            return "Case Study", 4
        elif section == "E":
            return "Long Answer (LA)", 5
        return "Unknown", 0

    def extract_questions(self, text_content: str, source_file: str) -> List[QuestionModel]:
        """
        Parses cleaned text and extracts list of QuestionModel objects.
        """
        lines = text_content.splitlines()
        questions: List[QuestionModel] = []
        
        current_section = "A" # Default start section
        
        # Temp variables for accumulating current question
        current_q_no: Optional[int] = None
        current_q_lines: List[str] = []
        current_options: Dict[str, List[str]] = {}
        active_option: Optional[str] = None

        def finalize_current_question():
            nonlocal current_q_no, current_q_lines, current_options, active_option
            if current_q_no is None:
                return
                
            q_section = self.get_section_from_no(current_q_no)
            q_type, q_marks = self.get_type_and_marks(current_q_no, q_section)
            
            # Combine question text lines
            question_text = "\n".join(current_q_lines).strip()
            
            # Format options nicely
            formatted_options = {}
            for opt_letter, opt_lines in current_options.items():
                formatted_options[opt_letter] = "\n".join(opt_lines).strip()
                
            # Create question model
            q_model = QuestionModel(
                question_no=current_q_no,
                source_file=source_file,
                section=q_section,
                type=q_type,
                marks=q_marks,
                chapter=None,
                question=question_text,
                options=formatted_options
            )
            questions.append(q_model)
            
            # Reset
            current_q_no = None
            current_q_lines = []
            current_options = {}
            active_option = None

        for line in lines:
            # Check for section header change
            section_match = self.section_pattern.match(line)
            if section_match:
                # Update current section
                current_section = section_match.group(1).upper()
                continue

            # Check for question number start (e.g. "1.")
            q_start_match = self.question_start_pattern.match(line)
            if q_start_match:
                # Save previous question before starting new one
                finalize_current_question()
                current_q_no = int(q_start_match.group(1))
                active_option = None
                continue

            # If we are inside a question block
            if current_q_no is not None:
                # Check for option header (e.g., "(A)")
                opt_parse = self.parser.parse_option_line(line)
                if opt_parse:
                    opt_letter, opt_text = opt_parse
                    active_option = opt_letter
                    current_options[opt_letter] = [opt_text] if opt_text else []
                else:
                    # Append content
                    if active_option:
                        current_options[active_option].append(line)
                    else:
                        current_q_lines.append(line)
            else:
                # Text outside any question block (e.g. instructions at top of section)
                # Check if it contains general instructions, otherwise just ignore
                pass

        # Finalize the last question
        finalize_current_question()
        
        # Sort questions by question_no
        questions.sort(key=lambda q: q.question_no)
        return questions
