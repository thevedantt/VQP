"""Shared prompt construction and response normalization for AI question generation.

Used by both ``OpenRouterService`` (primary) and ``GeminiService`` (secondary
fallback) so the two providers are prompted identically and their JSON
responses are normalized into the same shape consumed by ``paper_service.py``.
"""

from __future__ import annotations

from typing import Any

from app.models.enums import DifficultyLevel, DiagramType, QuestionType

_MCQ_TYPES = {"MCQ", "Assertion Reason"}

# Explicit, diagram-detector-friendly instructions used to steer the model
# toward producing a question that naturally requires the given diagram type.
# Each phrase intentionally contains the exact wording the heuristic
# classifier in diagram_service.py looks for (e.g. "free body diagram",
# "circuit diagram"), so detection succeeds even if the model only partially
# follows instructions.
_DIAGRAM_PHRASES: dict[str, str] = {
    "free_body": "Draw the free body diagram of the object, clearly labeling all the forces acting on it.",
    "circuit": "Draw the circuit diagram for the given arrangement, clearly labeling all components.",
    "ray_diagram": "Draw the ray diagram showing the formation of the image.",
    "graph": "Draw the graph showing the variation described, with clearly labeled axes.",
    "magnetic_field": "Sketch the magnetic field lines for the given configuration, clearly indicating their direction.",
}

_VALID_DIAGRAM_TYPES: set[str] = set(_DIAGRAM_PHRASES) | {"none"}

_TYPE_INSTRUCTIONS: dict[str, str] = {
    "MCQ": (
        "Write a single multiple-choice question with exactly four options "
        'labeled "A", "B", "C", "D" in the "options" object. Exactly one option must be correct.'
    ),
    "Assertion Reason": (
        "Write an Assertion-Reason question. The 'question' field must contain an "
        "'Assertion (A):' statement followed by a 'Reason (R):' statement. Provide the "
        "standard CBSE four-option set in 'options' (A: both A and R are true and R is the "
        "correct explanation of A; B: both A and R are true but R is not the correct "
        "explanation of A; C: A is true but R is false; D: A is false but R is true)."
    ),
    "VSA": "Write a Very Short Answer question that can be answered in 1-2 sentences or a short calculation.",
    "SA": "Write a Short Answer question that requires a brief explanation and/or a short derivation or numerical.",
    "LA": "Write a Long Answer question that requires a detailed derivation, explanation, or multi-part numerical solution.",
    "Case Study": (
        "Write a Case Study question: a short passage (2-4 sentences) describing a real-world "
        "or experimental scenario grounded in the NCERT content, followed by 2-3 sub-questions "
        "labeled (i), (ii), (iii) based on that passage."
    ),
}


def build_question_prompt(
    chapter: str,
    difficulty: DifficultyLevel,
    marks: int,
    question_type: QuestionType,
    context: str,
    require_diagram: bool = False,
    diagram_type_hint: DiagramType | None = None,
) -> str:
    """Build the full CBSE question-generation prompt for an LLM provider."""

    type_instructions = _TYPE_INSTRUCTIONS.get(
        question_type, "Write a question appropriate for the given marks and difficulty."
    )

    diagram_instruction = ""
    diagram_schema = ""
    if require_diagram and diagram_type_hint and diagram_type_hint != "none":
        phrase = _DIAGRAM_PHRASES.get(diagram_type_hint, "")
        diagram_instruction = f"""
- This question MUST require the student to draw a diagram. Include the following
  instruction verbatim as part of the "question" text: "{phrase}"
- Describe a specific, concrete scenario (the objects, forces, circuit components,
  optical setup, or quantities involved) so the diagram is meaningful and can be
  drawn directly from the question text."""
        diagram_schema = f""",
  "diagram": {{
    "diagram_type": "{diagram_type_hint}",
    "scenario": "<short snake_case scenario name, e.g. center_tapped_rectifier>",
    "entities": ["<diagram entity 1>", "<diagram entity 2>", "..."]
  }}"""

    return f"""You are an expert CBSE Class 12 Physics paper setter.

Using ONLY the NCERT textbook excerpt below as grounding material, write ONE brand-new
{difficulty}-difficulty question for the chapter "{chapter}" worth {marks} mark(s).

Requirements:
- {type_instructions}
- The question must be original CBSE-board-exam style wording. Do not copy sentences verbatim
  from the excerpt; rephrase and apply the concepts.
- The question must be solvable using only the concepts present in the excerpt.
- Keep the "question" field self-contained (include any numerical data needed to solve it).{diagram_instruction}

NCERT excerpt:
\"\"\"
{context}
\"\"\"

Respond with ONLY a JSON object matching this schema (no markdown, no commentary):
{{
  "question": "<full question text>",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "marks": {marks},
  "chapter": "{chapter}",
  "type": "{question_type}",
  "concept": "<short concept name this question tests>"{diagram_schema}
}}

If the question type does not require options, return "options" as an empty object {{}}.
"""


def normalize_question_response(
    data: dict[str, Any],
    chapter: str,
    difficulty: DifficultyLevel,
    marks: int,
    question_type: QuestionType,
    diagram_type_hint: DiagramType | None = None,
) -> dict[str, Any]:
    """Validate/normalize a provider's parsed JSON response into a uniform dict.

    Also extracts the optional ``diagram`` object (concept-extraction data
    embedded in the same generation call for AI-generated diagram questions)
    into ``diagram_entities``/``diagram_scenario``.
    """

    question_text = (data.get("question") or "").strip()
    if not question_text:
        raise ValueError("Model response is missing a non-empty 'question' field.")

    options = data.get("options") or {}
    if not isinstance(options, dict):
        options = {}
    if question_type not in _MCQ_TYPES:
        options = {}

    diagram_entities: list[str] = []
    diagram_scenario: str | None = None
    diagram = data.get("diagram")
    if isinstance(diagram, dict):
        entities = diagram.get("entities")
        if isinstance(entities, list):
            diagram_entities = [str(e) for e in entities if str(e).strip()]
        scenario = diagram.get("scenario")
        if isinstance(scenario, str) and scenario.strip():
            diagram_scenario = scenario.strip()

    return {
        "question": question_text,
        "options": {str(k): str(v) for k, v in options.items()},
        "marks": int(data.get("marks") or marks),
        "chapter": data.get("chapter") or chapter,
        "type": question_type,
        "difficulty": difficulty,
        "concept": data.get("concept"),
        "diagram_entities": diagram_entities,
        "diagram_scenario": diagram_scenario,
    }


def build_concept_extraction_prompt(question_text: str) -> str:
    """Build a prompt asking an LLM to extract concept/diagram metadata from a question."""

    diagram_types = ", ".join(sorted(_VALID_DIAGRAM_TYPES))
    return f"""You are an expert CBSE Class 12 Physics paper analyst.

Analyze the following question and identify its core concept and diagram requirements.

Question:
\"\"\"
{question_text}
\"\"\"

Respond with ONLY a JSON object matching this schema (no markdown, no commentary):
{{
  "chapter": "<NCERT Class 12 Physics chapter name this question belongs to>",
  "concept": "<short snake_case concept name, e.g. full_wave_rectifier>",
  "diagram_type": "<one of: {diagram_types}>",
  "scenario": "<short snake_case scenario name, or null if no diagram is needed>",
  "entities": ["<diagram entity 1>", "<diagram entity 2>", "..."],
  "confidence": <number between 0 and 1>
}}

If the question does not require a diagram, set "diagram_type" to "none", "scenario" to null,
and "entities" to an empty array.
"""


def build_physics_analysis_prompt(question_text: str, vocabulary: str) -> str:
    """Build a prompt asking an LLM to perform physics understanding ONLY (no geometry).

    This is the entry point of the Physics Semantic Diagram Intelligence
    pipeline: the model identifies *what* the diagram is about (diagram type,
    concept, scenario, entities) using only the vocabulary supplied by the
    diagram taxonomy. It must NEVER produce coordinates, pixel positions,
    angles, sizes, or SVG/markup - all geometry is computed deterministically
    downstream by ``SchemaPopulationService``.
    """

    return f"""You are a CBSE Class 12 Physics concept analyst. Your ONLY job is to identify
the physics concept and scenario behind a question - you do NOT design or draw the diagram.

IMPORTANT RULES:
- You MUST NEVER output coordinates, x/y positions, pixel values, angles, sizes, geometry, or SVG.
- You MUST choose "diagram_type", "concept", and "scenario" ONLY from the vocabulary below.
- If nothing in the vocabulary matches, set "concept" and "scenario" to null.

Vocabulary (diagram_type: concept (scenarios: ...)):
{vocabulary}

Question:
\"\"\"
{question_text}
\"\"\"

Respond with ONLY a JSON object matching this schema (no markdown, no commentary):
{{
  "diagram_required": <true or false>,
  "diagram_type": "<one of: {", ".join(sorted(_VALID_DIAGRAM_TYPES))}>",
  "chapter": "<NCERT Class 12 Physics chapter name this question belongs to, or null>",
  "concept": "<concept name from the vocabulary above, or null>",
  "scenario": "<scenario name from the vocabulary above, or null>",
  "entities": ["<diagram entity 1>", "<diagram entity 2>", "..."],
  "confidence": <number between 0 and 1>
}}

If the question does not require a diagram, set "diagram_required" to false, "diagram_type" to
"none", "concept" and "scenario" to null, and "entities" to an empty array.
"""
