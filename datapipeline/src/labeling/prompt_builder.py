from typing import Dict, Any

class PromptBuilder:
    """
    Constructs prompts for local LLM to label CBSE Physics question metadata.
    """

    def build_system_prompt(self) -> str:
        return """You are a CBSE Class 12 Physics expert.

Analyze the following Physics question and return ONLY valid JSON.

Rules:
* Return ONLY JSON.
* No markdown.
* No explanations.
* No code blocks.
* No additional text.
* Every field must be populated.
* If no diagram is required, set:
  "requires_diagram": false
  "diagram_type": "none"

Valid Chapters:
* Electric Charges and Fields
* Electrostatic Potential and Capacitance
* Current Electricity
* Moving Charges and Magnetism
* Magnetism and Matter
* Electromagnetic Induction
* Alternating Current
* Electromagnetic Waves
* Ray Optics
* Wave Optics
* Dual Nature of Radiation and Matter
* Atoms
* Nuclei
* Semiconductor Electronics

Output Schema:
{
  "chapter": "",
  "concept": "",
  "difficulty": "easy | medium | hard",
  "requires_diagram": false,
  "diagram_type": "none"
}"""

    def build_user_prompt(self, question: Dict[str, Any]) -> str:
        question_text = question.get("question", "")
        options = question.get("options", {})
        
        prompt_lines = [
            f"Question:\n{question_text}"
        ]
        
        if options:
            prompt_lines.append("Options:")
            for opt_letter, opt_text in options.items():
                prompt_lines.append(f"({opt_letter}) {opt_text}")
                
        return "\n".join(prompt_lines)

