import re
from collections import Counter
from typing import Dict, Any, List, Set

def analyze_text_metrics(text: str) -> Dict[str, Any]:
    """
    Computes text statistics, language ratios, question patterns,
    readability and reliability scores, and classifies status.
    """
    metrics = {}
    
    char_count = len(text)
    metrics["char_count"] = char_count
    
    # Early exit for empty or very short files
    if char_count < 10:
        return {
            "char_count": char_count,
            "word_count": 0,
            "line_count": 0,
            "english_percentage": 0.0,
            "hindi_percentage": 0.0,
            "corrupted_char_percentage": 0.0,
            "special_char_percentage": 0.0,
            "question_pattern_count": 0,
            "readability_score": 0,
            "reliability_score": 0,
            "status": "Poor",
            "issues": ["Empty or extremely short content"]
        }

    # Word and Line Counts
    words = text.split()
    word_count = len(words)
    metrics["word_count"] = word_count
    
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    line_count = len(lines)
    metrics["line_count"] = line_count

    # Language counts (Hindi vs English)
    # Hindi (Devanagari): \u0900 to \u097F
    hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097f')
    # English: a-z, A-Z
    english_chars = sum(1 for c in text if ('a' <= c <= 'z') or ('A' <= c <= 'Z'))
    
    metrics["english_percentage"] = round((english_chars / char_count) * 100, 2)
    metrics["hindi_percentage"] = round((hindi_chars / char_count) * 100, 2)

    # Corrupted characters (e.g., \ufffd or odd control characters)
    # Control chars excluding \n, \r, \t
    corrupted_count = sum(1 for c in text if c == '\ufffd' or (ord(c) < 32 and c not in '\n\r\t'))
    metrics["corrupted_char_percentage"] = round((corrupted_count / char_count) * 100, 2)

    # Special characters: non-alphanumeric, non-space, non-Devanagari, non-standard punctuation
    special_char_count = 0
    # Allow alphanumeric, spaces, standard punctuations, devanagari characters, and basic math symbols
    allowed_pattern = re.compile(r'[a-zA-Z0-9\s.,;:!?()\'"\-\[\]{}*=+\u0900-\u097f]')
    special_char_count = sum(1 for c in text if not allowed_pattern.match(c))
    metrics["special_char_percentage"] = round((special_char_count / char_count) * 100, 2)

    # Question Pattern Detection
    # Standard question identifiers like "Q. 1", "Question 12", "Section A", "OR"
    question_patterns = [
        r'\bQ\s*\.?\s*\d+\b',              # Q. 1, Q1, Q. 12
        r'\bQ(?:uestion)?\s+\d+\b',        # Question 5
        r'\bSECTION\s+[A-E]\b',            # SECTION A
        r'\bSection\s+[A-E]\b',            # Section B
        r'\b(?:OR|Or)\b',                  # OR choices
        r'\(\s*[a-z]\s*\)',                # (a), (b), (c)
        r'\(\s*[i|v|x]+\s*\)'             # (i), (ii), (iv)
    ]
    
    pattern_count = 0
    for pat in question_patterns:
        pattern_count += len(re.findall(pat, text, re.IGNORECASE))
    metrics["question_pattern_count"] = pattern_count

    # Issues detection
    issues = []
    if metrics["corrupted_char_percentage"] > 0.2:
        issues.append("Unicode corruption detected")
    
    # If character count is high but word count is suspiciously low
    if char_count > 1000 and word_count < 50:
        issues.append("Potential font encoding problems (low word density)")

    if metrics["special_char_percentage"] > 8.0:
        issues.append("Excessive special characters")

    # Detect repeated headers/footers
    repeated_lines_count = 0
    line_freqs = Counter(lines)
    # If a non-trivial line appears more than 3 times, it's likely a header/footer
    headers_footers = []
    for line, count in line_freqs.items():
        if len(line) > 10 and count > 3:
            headers_footers.append(line)
            repeated_lines_count += count * len(line)

    if headers_footers:
        issues.append(f"Repeated headers/footers detected: {len(headers_footers)} unique patterns")

    # Readability Score
    # Sentence estimate: split by period, exclamation, question mark, or Devanagari full stop (। - \u0964)
    sentences = re.split(r'[.!?\u0964]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    
    avg_sent_len = word_count / max(1, sentence_count)
    avg_word_len = char_count / max(1, word_count)
    
    # Heuristic formula for Readability score (0-100)
    # Long sentences and long words reduce readability.
    readability = 100 - (avg_sent_len * 0.35) - (avg_word_len * 7.5)
    metrics["readability_score"] = int(max(0, min(100, readability)))

    # Reliability Score
    # Start at 100 and deduct for quality issues
    reliability = 100.0
    reliability -= metrics["corrupted_char_percentage"] * 30.0
    reliability -= metrics["special_char_percentage"] * 2.0
    
    if len(headers_footers) > 5:
        reliability -= 10.0
    if word_count < 100:
        reliability -= 20.0
    
    # Penalize if no question patterns are found in a supposedly long document
    if char_count > 1000 and pattern_count == 0:
        reliability -= 15.0

    metrics["reliability_score"] = int(max(0, min(100, reliability)))

    # Determine status
    # Excellent: Readability >= 80, Reliability >= 90
    # Good: Readability >= 65, Reliability >= 75
    # Needs Cleaning: Reliability >= 50
    # Poor: Otherwise
    read = metrics["readability_score"]
    rel = metrics["reliability_score"]
    
    if read >= 80 and rel >= 90:
        status = "Excellent"
    elif read >= 65 and rel >= 75:
        status = "Good"
    elif rel >= 50:
        status = "Needs Cleaning"
    else:
        status = "Poor"
        
    metrics["status"] = status
    metrics["issues"] = issues

    return metrics
