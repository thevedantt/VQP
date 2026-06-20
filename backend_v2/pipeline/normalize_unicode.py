"""
Unicode normalization for CBSE PYQ text - Phase 3B Task 1.

Single source of truth for the PDF-extraction cleanup previously
duplicated between data/build_descriptive_dataset.py and
data/build_mcq_dataset.py:

    1. decode_symbols()     - the embedded Symbol-style font's glyphs,
                               extracted into Private-Use-Area codepoints
                               (U+F0xx), mapped back to real characters
                               (mu, Omega, pi, theta, ...), verified
                               empirically against the underlying physics.
    2. fix_scientific_notation() - "A x 10<exp>" with the exponent glued
                               on in plain digits (e.g. "9 x 105") is
                               rewritten with a proper superscript
                               exponent ("9 x 10^5").
    3. strip_paper_artifacts() - paper-level instructions that bled into
                               the last question of a section during PDF
                               extraction (e.g. "Questions number 29 and
                               30 are Case Study-based questions. Read
                               the following paragraphs...") are cut.
    4. is_clean()              - true if no unmapped Private-Use-Area
                               artifact remains.

normalize(text) runs all of the above and is what both the dataset
builders and the question selector (for defense-in-depth on AI output)
should call.
"""

import re

# ---------------------------------------------------------------------------
# Task 1: Symbol-font Private-Use-Area decode table.
# ---------------------------------------------------------------------------
# Each mapping was verified against the underlying physics, e.g.:
#   - mu_0*I/(2*pi*a)                              -> U+F06D/U+F070 = mu/pi
#   - epsilon*mu in the EM wave-speed relation      -> U+F065/U+F06D
#   - "3 Ohm" resistor values                       -> U+F057 = Omega
#   - delta_m in prism-deviation problems           -> U+F064 = delta
#   - magnetic susceptibility chi in -1 < chi < 0   -> U+F063 = chi
#   - resistivities rho1 + rho2                     -> U+F072 = rho
#   - m/n = c, beta/alpha != c                      -> U+F061/U+F062/U+F0B9
#   - 1.7 x 10-7 m2 (scientific notation)            -> U+F025/U+F0B4 = times
# Codes with no standalone meaning once flattened from layout (vector-arrow
# and hat accents, section-break bleed-over, stray trailing artifacts,
# stacked-fraction paren pieces) are stripped rather than mapped.
SYMBOL_FONT_MAP = {
    "": "×",  # multiplication (scientific notation)
    "": "Ω",  # Omega (ohm)
    "": "Δ",  # Delta (uppercase)
    "": "δ",  # delta
    "": "ε",  # epsilon
    "": "φ",  # phi
    "": "λ",  # lambda
    "": "μ",  # mu
    "": "π",  # pi
    "": "θ",  # theta
    "": "σ",  # sigma
    "": "τ",  # tau
    "": "ω",  # omega
    "": "°",  # degree
    "": "α",  # alpha
    "": "β",  # beta
    "": "χ",  # chi (magnetic susceptibility)
    "": "ν",  # nu
    "": "ρ",  # rho (resistivity)
    "": "<",        # less-than (ratio comparison options)
    "": ">",        # greater-than
    "": "×",  # multiplication (scientific notation, alt code)
    "": "≠",  # not-equal
    "": "",          # stray trailing artifact
    "": "",          # section-break bleed-over
    "": "",          # vector-arrow accent piece
    "": "",          # hat/circumflex accent piece
    "": "", "": "", "": "",  # stacked-fraction paren pieces
    "": "", "": "", "": "",
}

_SUPERSCRIPT_DIGITS = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
}
_SUPERSCRIPT_SIGNS = {"-": "⁻", "−": "⁻", "–": "⁻", "+": "⁺"}

# "A (x|times) 10<sign?><digits>" with the exponent glued on in plain
# digits, e.g. "9 x 105" (-> 9 x 10^5) or "1.7 x 10-7" (-> 1.7 x 10^-7).
# Sign may be a proper minus (U+2212), an en dash (U+2013, used
# interchangeably as a minus in some source papers), or a plain hyphen.
_SCI_NOTATION_RE = re.compile(r"(?<=[×x])(\s?)10([+−–-]?)(\d{1,3})\b")

# Paper-level instructions that bled into the previous question's text
# during PDF extraction - always trailing, so matched through end-of-string.
_ARTIFACT_PATTERNS = [
    re.compile(
        r"\s*Questions?\s+number\s+\d+\s+and\s+\d+\s+are\b.*$",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\s*SECTION\s*[–‒-]\s*[A-E]\b.*$",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\s*All questions are compulsory\.?.*$",
        re.IGNORECASE | re.DOTALL,
    ),
]


def decode_symbols(text):
    if not text:
        return text
    for code, char in SYMBOL_FONT_MAP.items():
        text = text.replace(code, char)
    return text


def fix_scientific_notation(text):
    if not text:
        return text

    def _superscript(match):
        leading_space, sign, digits = match.group(1), match.group(2), match.group(3)
        sup = "".join(_SUPERSCRIPT_DIGITS[d] for d in digits)
        if sign:
            sup = _SUPERSCRIPT_SIGNS[sign] + sup
        return leading_space + "10" + sup

    return _SCI_NOTATION_RE.sub(_superscript, text)


def strip_paper_artifacts(text):
    if not text:
        return text
    for pattern in _ARTIFACT_PATTERNS:
        text = pattern.sub("", text)
    return text.strip()


def is_clean(text):
    """True if no unmapped Private-Use-Area artifact remains."""
    return bool(text) and not any(0xE000 <= ord(c) <= 0xF8FF for c in text)


def normalize(text):
    """Full pipeline: symbol decode -> scientific notation -> artifact strip."""
    if not text:
        return text
    text = decode_symbols(text)
    text = fix_scientific_notation(text)
    text = strip_paper_artifacts(text)
    return text
