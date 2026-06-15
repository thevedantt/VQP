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


def build_physics_analysis_prompt(question_text: str, vocabulary: str) -> str:
    """Build a prompt that turns the LLM into a "Physics Semantic Analyst".

    This is the entry point of the Dynamic Physics Semantic Schema pipeline:

        Question -> PhysicsAnalyzerService -> Semantic Schema -> Template Selection
                 -> SchemaPopulationService -> Render Schema -> SVG

    The model does NOT design or draw the diagram. For every question it must:
      1. Understand the question.
      2. Explain what the question is asking.
      3. Identify the underlying physics concept.
      4. Determine why a diagram is required (or why not).
      5. Identify what components/entities must appear in the diagram.
      6. Identify what labels must appear in the diagram.
      7. Emit a dynamic, concept-specific semantic schema.

    It must NEVER produce coordinates, pixel positions, angles, sizes, or
    SVG/markup - all geometry is computed deterministically downstream by
    ``SchemaPopulationService`` and ``diagram_generators``. The "extra" block
    is the one place the model can be concept-specific: it should contain
    whatever categorical (non-numeric) facts a renderer for THIS concept
    would need, modeled on the worked examples below.
    """

    diagram_types = ", ".join(sorted(_VALID_DIAGRAM_TYPES))

    return f"""You are a CBSE Class 12 Physics Semantic Analyst. You do NOT design or draw
diagrams - your job is to read a question, understand it deeply, and emit a dynamic,
concept-specific semantic schema that downstream renderers will consume.

For every question, work through these steps before answering:
1. Understand the question - what is it actually asking the student to do?
2. Explain, in plain language, what the question is asking.
3. Identify the underlying physics concept (and chapter) involved.
4. Decide WHY a diagram is required (or, if not, why not).
5. Identify what components/entities MUST appear in the diagram.
6. Identify what labels MUST appear in the diagram.
7. Generate the dynamic semantic schema described below.

IMPORTANT RULES:
- You MUST NEVER output coordinates, x/y positions, pixel values, angles, sizes, geometry, or SVG.
- Prefer "diagram_type", "concept", and "scenario" names from the vocabulary below. If nothing
  fits well, you may propose a new snake_case concept/scenario name - list it in
  "candidate_concepts" so it can be reviewed, but still pick the closest "diagram_type".
- If nothing matches at all, set "concept" and "scenario" to null and leave "candidate_concepts"
  with your best proposed name(s).
- "extra" is a free-form, CONCEPT-SPECIFIC object. Its shape should change depending on the
  concept - do not force every concept into the same fields. Use the worked examples below as a
  guide for the KIND of categorical (non-numeric) information to include, not as a fixed schema.

Vocabulary (diagram_type: concept (scenarios: ...)):
{vocabulary}

Question:
\"\"\"
{question_text}
\"\"\"

Respond with ONLY a JSON object matching this schema (no markdown, no commentary):
{{
  "chapter": "<NCERT Class 12 Physics chapter name this question belongs to, or null>",
  "concept": "<concept name, preferably from the vocabulary above, or null>",
  "scenario": "<scenario name, preferably from the vocabulary above, or null>",
  "diagram_type": "<one of: {diagram_types}>",
  "diagram_required": <true or false>,
  "confidence": <number between 0 and 1>,
  "candidate_concepts": ["<alternative or newly proposed concept name(s)>"],
  "required_entities": ["<diagram component/entity 1>", "<...>"],
  "relationships": ["<how the entities relate to each other, e.g. 'lens forms image of object on the opposite side'>"],
  "constraints": ["<physical constraints the diagram must respect, e.g. 'image must be real and inverted'>"],
  "visual_rules": ["<rules the renderer must follow, e.g. 'draw two construction rays from the top of the object'>"],
  "validation": ["<checks an examiner would use to mark the diagram correct, e.g. 'all forces must be labeled with arrows'>"],
  "understanding": {{
    "what_is_the_question_asking": "<plain-language restatement of the task>",
    "what_physics_concept_is_involved": "<the core concept, in plain language>",
    "why_is_a_diagram_required": "<why a diagram is (or is not) needed to answer this>",
    "what_must_be_visible": ["<thing 1 that must be visible in the diagram>", "<...>"],
    "what_labels_must_be_present": ["<label 1>", "<label 2>", "..."],
    "what_examiner_expects_to_see": "<what a CBSE examiner would expect a correct diagram to show>"
  }},
  "extra": {{ ... concept-specific fields, see examples below ... }}
}}

WORKED EXAMPLES of "extra" (these illustrate the KIND of concept-specific information expected -
adapt the field names and values to the actual concept of the current question):

- Ray Diagram (e.g. convex lens, object between F and 2F):
  "extra": {{
    "lens_type": "convex",
    "object_position": "between_f_and_2f",
    "expected_image": "real_inverted_magnified",
    "ray_rules": ["parallel_ray", "optical_center_ray"]
  }}

- Full Wave Rectifier (circuit):
  "extra": {{
    "rectifier_type": "center_tapped",
    "number_of_diodes": 2,
    "requires_transformer": true,
    "requires_load_resistor": true,
    "ac_source": true,
    "dc_output": true
  }}

- Free Body Diagram (block on an inclined plane with friction):
  "extra": {{
    "surface": "inclined",
    "object": "block",
    "forces": ["weight", "normal_reaction", "friction", "tension"]
  }}

- Graph (e.g. photoelectric effect, stopping potential vs frequency):
  "extra": {{
    "graph_type": "stopping_potential_vs_frequency",
    "x_axis": "frequency",
    "y_axis": "stopping_potential",
    "curve_shape": "linear_with_intercept"
  }}

If the question does NOT require a diagram, set "diagram_required" to false, "diagram_type" to
"none", "concept" and "scenario" to null, "required_entities"/"relationships"/"constraints"/
"visual_rules"/"validation" to empty arrays, "extra" to an empty object {{}}, but still fill in
"understanding" - in particular, "why_is_a_diagram_required" must explain why no diagram is
needed for this question.
"""
