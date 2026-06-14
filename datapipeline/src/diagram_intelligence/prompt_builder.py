from typing import Dict, Any

class PromptBuilder:
    """
    Constructs prompts targeting diagram intelligence analysis of questions.
    """

    def build_system_prompt(self) -> str:
        return """You are a CBSE Class 12 Physics expert specializing in question diagram intelligence.
Evaluate the given Physics question to determine if a diagram is required to solve it or if it explicitly requests drawing, and classify the diagram type.

Rules:
* Return ONLY valid JSON.
* No markdown wrappers.
* No code blocks.
* No explanations outside the JSON structure.

Diagram Rules:
- requires_diagram = true ONLY if:
  1. The question text explicitly requests to: draw, sketch, graph, plot, or construct.
  2. Visualization (drawing a diagram) is essential to solve or explain the answer correctly.
- Otherwise, requires_diagram must be false.

Supported Diagram Types:
- free_body (forces, vectors, tension, mechanics)
- circuit (resistors, capacitors, diodes, LCR, battery, electrical circuits)
- graph (plots of voltage-current, photoelectric intensity-potential, magnetic field variation, etc.)
- ray_diagram (lenses, mirrors, prisms, refraction/reflection paths)
- optical_instrument (telescope, microscope ray paths, compound lens configurations)
- magnetic_field (field lines around coils, solenoids, charge paths in magnetic fields)
- none (if no diagram is required)

Confidence Rules:
- 0.95 = explicitly asks to draw, sketch, plot, construct.
- 0.75 = visualization strongly recommended to solve.
- 0.50 = uncertain.

Output JSON Schema:
{
  "requires_diagram": true | false,
  "diagram_type": "free_body | circuit | graph | ray_diagram | optical_instrument | magnetic_field | none",
  "confidence": 0.0 - 1.0,
  "reason": "short explanation of the classification"
}"""

    def build_user_prompt(self, question: Dict[str, Any]) -> str:
        question_text = question.get("question", "")
        options = question.get("options", {})
        
        prompt_lines = [
            f"Question Text: {question_text}"
        ]
        
        if options:
            prompt_lines.append("Options:")
            for opt_letter, opt_text in options.items():
                prompt_lines.append(f"({opt_letter}) {opt_text}")
                
        return "\n".join(prompt_lines)
