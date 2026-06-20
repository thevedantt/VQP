"""
CBSE paper templates.

A template is a list of sections; each section is a list of "blocks"
(one question type at one mark value). diagram_quota on a block is
either:
    {"min": N}      - hard requirement, logged as a failure if unmet
    {"prefer": N}   - best-effort target, not fatal if unmet

These are intentionally plain data (no hardcoded ratios) so the
frontend can drive template selection while question_selector.py
controls PYQ/AI ratio, chapter filters, and difficulty separately.
"""

TEMPLATES = {
    "UNIT_TEST_20": {
        "template_id": "UNIT_TEST_20",
        "title": "Unit Test",
        "total_marks": 20,
        "sections": [
            {
                "section_id": "UNIT",
                "name": None,
                "blocks": [
                    {"type": "MCQ", "count": 2, "marks_each": 1, "diagram_quota": None},
                    {"type": "Fill in the Blanks", "count": 2, "marks_each": 1, "diagram_quota": None},
                    {"type": "Very Short", "count": 2, "marks_each": 2, "diagram_quota": None},
                    {"type": "Short Answer", "count": 2, "marks_each": 3, "diagram_quota": {"min": 1}},
                    {"type": "Long Answer", "count": 1, "marks_each": 6, "diagram_quota": {"prefer": 1}},
                ],
            },
        ],
    },
    "CBSE_70": {
        "template_id": "CBSE_70",
        "title": "CBSE Physics Paper",
        "total_marks": 70,
        "sections": [
            {
                "section_id": "A",
                "name": "Section A",
                "blocks": [
                    {"type": "MCQ", "count": 10, "marks_each": 1, "diagram_quota": None},
                    {"type": "Assertion Reason", "count": 6, "marks_each": 1, "diagram_quota": None},
                ],
            },
            {
                "section_id": "B",
                "name": "Section B",
                "blocks": [
                    {"type": "Very Short", "count": 5, "marks_each": 2, "diagram_quota": None},
                ],
            },
            {
                "section_id": "C",
                "name": "Section C",
                "blocks": [
                    {"type": "Short Answer", "count": 7, "marks_each": 3, "diagram_quota": {"min": 2}},
                ],
            },
            {
                "section_id": "D",
                "name": "Section D",
                "blocks": [
                    {"type": "Case Study", "count": 2, "marks_each": 4, "diagram_quota": {"prefer": 1}},
                ],
            },
            {
                "section_id": "E",
                "name": "Section E",
                "blocks": [
                    {"type": "Long Answer", "count": 3, "marks_each": 5, "diagram_quota": {"min": 1}},
                ],
            },
        ],
    },
}


def get_template(template_name):
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
    return TEMPLATES[template_name]


def list_templates():
    return list(TEMPLATES.keys())


def total_question_count(template):
    return sum(
        block["count"]
        for section in template["sections"]
        for block in section["blocks"]
    )


def hard_diagram_minimum(template):
    """Sum of all hard ('min') diagram quotas across the template."""
    total = 0
    for section in template["sections"]:
        for block in section["blocks"]:
            quota = block.get("diagram_quota") or {}
            total += quota.get("min", 0)
    return total
