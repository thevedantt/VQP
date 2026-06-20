"""
Reflow raw question text into a clean hierarchical structure for PDF export.

PYQ-sourced question text was extracted line-by-line from the original
paper's PDF, so a single sentence is broken across several lines purely
because of where the *original* page happened to wrap it - those breaks
mean nothing in a freshly laid-out document and, left as hard line
breaks, are exactly what makes exported PDFs look like raw extraction
dumps instead of a typeset paper.

Within that text, CBSE numbering markers - (a)/(b) alternatives, OR,
lowercase-roman (i)/(ii) subparts, uppercase-roman (I)/(II) sub-subparts -
sit on their own line too, with their own text following on the next
line(s). parse_subparts() recovers the real structure: each marker
starts a new block, and bare continuation lines are rejoined with a
single space instead of a forced break.
"""

import re

_LEVEL0_RE = re.compile(r"^\(([ab])\)\s*(.*)$")
_LEVEL1_RE = re.compile(r"^\(([ivx]+)\)\s*(.*)$")
_LEVEL2_RE = re.compile(r"^\(([IVX]+)\)\s*(.*)$")
_OR_RE = re.compile(r"^OR$")


def parse_subparts(text):
    """Return a list of blocks: {"level": 0|1|2|None|"or", "label": str|None, "text": str}.

    level None with no other blocks means the question has no CBSE
    numbering markers at all - just plain (possibly wrapped) prose.
    """
    if not text:
        return []

    lines = [ln.strip() for ln in text.split("\n")]
    blocks = []
    current = None

    def flush():
        if current is not None:
            joined = " ".join(p for p in current["parts"] if p).strip()
            # Keep bare markers (e.g. a lone "(a)" whose real text only
            # starts under its first (i) child) - the label alone still
            # carries meaning and must render even with no body text.
            if joined or current["label"]:
                blocks.append({
                    "level": current["level"],
                    "label": current["label"],
                    "text": joined,
                })

    for line in lines:
        if not line:
            continue

        if _OR_RE.match(line):
            flush()
            blocks.append({"level": "or", "label": None, "text": "OR"})
            current = None
            continue

        m0 = _LEVEL0_RE.match(line)
        m1 = None if m0 else _LEVEL1_RE.match(line)
        m2 = None if (m0 or m1) else _LEVEL2_RE.match(line)

        if m0:
            flush()
            current = {"level": 0, "label": f"({m0.group(1)})", "parts": [m0.group(2)]}
        elif m1:
            flush()
            current = {"level": 1, "label": f"({m1.group(1)})", "parts": [m1.group(2)]}
        elif m2:
            flush()
            current = {"level": 2, "label": f"({m2.group(1)})", "parts": [m2.group(2)]}
        elif current is None:
            current = {"level": None, "label": None, "parts": [line]}
        else:
            current["parts"].append(line)

    flush()
    return blocks


def has_hierarchy(blocks):
    return any(b["level"] not in (None, "or") for b in blocks) if blocks else False
