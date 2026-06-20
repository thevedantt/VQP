"""
Renders a paper's JSON output into a clean PDF.

Handles both shapes:
    - Phase 2 (pipeline/paper_pipeline.py): flat question list, no
      section_id/marks/options.
    - Phase 3 (pipeline/paper_builder.py): section_id, marks, source,
      options, total_marks - rendered with section headers and marks.

Usage:
    python pipeline/pdf_export.py outputv2/papers/PAPER001.json
"""

import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

PIPELINE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = PIPELINE_DIR.parent
sys.path.insert(0, str(BACKEND_V2))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer
from svglib.svglib import svg2rlg

from pipeline.normalize_unicode import normalize
from pipeline.diagram_pipeline import resolve_compiled_svg
from pipeline.question_formatter import has_hierarchy, parse_subparts


OUTPUTV2_DIR = BACKEND_V2 / "outputv2"
PDF_OUTPUT_DIR = OUTPUTV2_DIR / "pdf_outputs"
PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONTS_DIR = BACKEND_V2 / "assets" / "fonts"

# Register a Unicode-coverage font so Greek letters (mu, Omega, theta, pi,
# Delta) and superscript exponents (10^-3) actually render in the PDF -
# the reportlab base-14 fonts (Helvetica etc.) don't cover them.
pdfmetrics.registerFont(TTFont("DejaVuSans", str(FONTS_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(FONTS_DIR / "DejaVuSans-Bold.ttf")))

STYLES = getSampleStyleSheet()
for _style_name in ("Title", "Heading2", "Heading3", "Heading4", "Normal", "BodyText"):
    STYLES[_style_name].fontName = "DejaVuSans"
STYLES["Title"].fontName = "DejaVuSans-Bold"
STYLES["Heading2"].fontName = "DejaVuSans-Bold"
STYLES["Heading3"].fontName = "DejaVuSans-Bold"
STYLES["Heading4"].fontName = "DejaVuSans-Bold"

PAGE_MARGIN = 2 * cm
CONTENT_HEIGHT = A4[1] - 2 * PAGE_MARGIN
# Tighter than before (was 0.6): a question+diagram KeepTogether block
# that doesn't fit in whatever space is left on the page gets pushed
# whole to the next page, leaving the remainder of the current page
# blank - keeping diagrams smaller makes that block more likely to fit.
MAX_DIAGRAM_HEIGHT = CONTENT_HEIGHT * 0.45

INSTRUCTIONS = (
    "All questions are compulsory. Marks for each question are indicated "
    "against it. Draw diagrams wherever necessary and label them clearly."
)

# One indented style per CBSE sub-part nesting level: (a)/(b) -> 0,
# (i)/(ii) -> 1, (I)/(II) -> 2.
_INDENT_PER_LEVEL = 0.7 * cm
SUBPART_STYLES = [
    ParagraphStyle(
        f"SubPart{lvl}",
        parent=STYLES["BodyText"],
        fontName="DejaVuSans",
        leftIndent=lvl * _INDENT_PER_LEVEL,
        spaceBefore=2,
        spaceAfter=2,
    )
    for lvl in range(3)
]
OR_STYLE = ParagraphStyle(
    "OrDivider",
    parent=STYLES["BodyText"],
    fontName="DejaVuSans-Bold",
    alignment=1,  # TA_CENTER
    spaceBefore=4,
    spaceAfter=4,
)
OPTION_STYLE = ParagraphStyle(
    "McqOption",
    parent=STYLES["BodyText"],
    fontName="DejaVuSans",
    leftIndent=0.4 * cm,
)


def _question_flowables(text):
    """Render question text as either one plain paragraph (no CBSE
    numbering markers found) or a nested, indented sequence of
    sub-part paragraphs - never as raw line-by-line extraction text."""
    blocks = parse_subparts(text)
    if not blocks:
        return [Paragraph(escape(normalize(text) or ""), STYLES["BodyText"])]

    if not has_hierarchy(blocks):
        return [Paragraph(escape(normalize(blocks[0]["text"])), STYLES["BodyText"])]

    flowables = []
    for b in blocks:
        if b["level"] == "or":
            flowables.append(Paragraph("OR", OR_STYLE))
            continue
        label = escape(b["label"]) if b["label"] else ""
        body = escape(normalize(b["text"]))
        content = f"<b>{label}</b> {body}".strip() if label else body
        style = SUBPART_STYLES[min(b["level"] or 0, 2)]
        flowables.append(Paragraph(content, style))
    return flowables


def _scaled_drawing(svg_path, max_width, max_height):
    drawing = svg2rlg(str(svg_path))
    if drawing is None or not drawing.width or not drawing.height:
        return None

    scale = min(1.0, max_width / drawing.width, max_height / drawing.height)
    drawing.scale(scale, scale)
    drawing.width *= scale
    drawing.height *= scale
    drawing.hAlign = "CENTER"
    return drawing


def _resolve_diagram_path(q, paper_id):
    """Prefer an explicit `diagram_path`; otherwise resolve by the
    family-aware paper_id/question_id naming convention used by the
    diagram engine (Phase 4.8, Issue 4). Only applies to questions
    actually flagged as needing a diagram - a stale SVG can otherwise
    sit at that path from an unrelated run."""
    if not q.get("diagram_required"):
        return None

    diagram_path = q.get("diagram_path")
    if diagram_path and Path(diagram_path).exists():
        return Path(diagram_path)

    if paper_id and q.get("question_id"):
        return resolve_compiled_svg(paper_id, q["question_id"])

    return None


def _append_question(story, q, content_width, paper_id):
    block = []

    label = q["question_id"]
    if q.get("marks") is not None:
        label = f"{label}  [{q['marks']} Mark{'s' if q['marks'] != 1 else ''}]"
    if q.get("source"):
        label = f"{label}  ({q['source']})"

    block.append(Paragraph(label, STYLES["Heading4"]))
    block.extend(_question_flowables(q.get("question", "")))

    options = q.get("options")
    if options:
        block.append(Spacer(1, 0.15 * cm))
        for k, v in options.items():
            opt_text = f"<b>({escape(str(k))})</b> {escape(normalize(str(v)))}"
            block.append(Paragraph(opt_text, OPTION_STYLE))
            block.append(Spacer(1, 0.12 * cm))

    diagram_path = _resolve_diagram_path(q, paper_id)
    if diagram_path:
        try:
            drawing = _scaled_drawing(diagram_path, content_width, MAX_DIAGRAM_HEIGHT)
            if drawing is not None:
                block.append(Spacer(1, 0.15 * cm))
                block.append(drawing)
        except Exception as e:
            block.append(Paragraph(f"[Diagram could not be rendered: {e}]", STYLES["BodyText"]))
    elif q.get("diagram_required") and q.get("diagram_status") not in (None, "SUCCESS"):
        error = q.get("diagram_error") or q.get("error")
        block.append(Paragraph(f"[Diagram generation failed: {error}]", STYLES["BodyText"]))

    block.append(Spacer(1, 0.6 * cm))

    # Keep the question, its options, and its diagram together so a page
    # break never lands between a question and its own diagram.
    story.append(KeepTogether(block))


def export_paper_to_pdf(paper_json_path):
    paper_json_path = Path(paper_json_path)

    with open(paper_json_path, "r", encoding="utf-8") as f:
        paper = json.load(f)

    paper_id = paper.get("paper_id", paper_json_path.stem)
    pdf_path = PDF_OUTPUT_DIR / f"{paper_id}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
    )
    content_width = A4[0] - 2 * PAGE_MARGIN

    story = [Paragraph(f"VisualQ Paper &mdash; {paper_id}", STYLES["Title"])]

    if paper.get("total_marks") is not None:
        story.append(Paragraph(f"Total Marks: {paper['total_marks']}", STYLES["Normal"]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Instructions", STYLES["Heading3"]))
    story.append(Paragraph(INSTRUCTIONS, STYLES["BodyText"]))
    story.append(Spacer(1, 0.5 * cm))

    questions = paper.get("questions", [])
    distinct_sections = {q.get("section_id") for q in questions if q.get("section_id")}
    has_sections = len(distinct_sections) > 1

    if has_sections:
        current_section = object()
        for q in questions:
            if q.get("section_id") != current_section:
                current_section = q.get("section_id")
                story.append(Paragraph(f"Section {current_section}", STYLES["Heading2"]))
                story.append(Spacer(1, 0.2 * cm))
            _append_question(story, q, content_width, paper_id)
    else:
        for q in questions:
            _append_question(story, q, content_width, paper_id)

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(
            A4[0] / 2, 1 * cm, f"VisualQ - {paper_id} - Page {doc_.page}"
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)

    return str(pdf_path)


def main():
    if len(sys.argv) > 1:
        paper_json = sys.argv[1]
    else:
        paper_json = input("Paper JSON path: ")

    pdf_path = export_paper_to_pdf(paper_json)
    print(f"PDF saved: {pdf_path}")


if __name__ == "__main__":
    main()
