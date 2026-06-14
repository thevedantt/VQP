import random
from pathlib import Path
from typing import List, Dict, Any

from utils.logger import logger

class MetadataSampler:
    """
    Selects validation samples from labeled questions ensuring diversity and coverage.
    """

    def sample_questions(self, questions: List[Dict[str, Any]], sample_size: int = 20, seed: int = 42) -> List[Dict[str, Any]]:
        """
        Samples questions focusing on chapter coverage and diagram inclusion.
        """
        if len(questions) <= sample_size:
            return questions

        random.seed(seed)
        
        # Separate diagram and non-diagram questions
        diagram_qs = [q for q in questions if q.get("requires_diagram")]
        non_diagram_qs = [q for q in questions if not q.get("requires_diagram")]

        # Determine target number of diagram questions (e.g. 5 out of 20, or a representative ratio)
        target_diagram_count = min(len(diagram_qs), 5)
        target_non_diagram_count = sample_size - target_diagram_count

        sampled_diagrams = random.sample(diagram_qs, target_diagram_count) if diagram_qs else []
        
        # To maximize chapter coverage, group non-diagram questions by chapter
        by_chapter = {}
        for q in non_diagram_qs:
            ch = q.get("chapter", "Unknown")
            by_chapter.setdefault(ch, []).append(q)

        sampled_non_diagrams = []
        chapters = list(by_chapter.keys())
        
        # Round-robin selection across chapters
        chapter_idx = 0
        while len(sampled_non_diagrams) < target_non_diagram_count and chapters:
            ch = chapters[chapter_idx % len(chapters)]
            if by_chapter[ch]:
                # Pop a random question from this chapter
                q_to_add = random.choice(by_chapter[ch])
                by_chapter[ch].remove(q_to_add)
                sampled_non_diagrams.append(q_to_add)
            else:
                # Remove exhausted chapter
                chapters.remove(ch)
                continue
            chapter_idx += 1

        # Fallback if we still need more questions
        remaining_needed = target_non_diagram_count - len(sampled_non_diagrams)
        if remaining_needed > 0:
            flat_remaining = [q for ch_list in by_chapter.values() for q in ch_list]
            sampled_non_diagrams.extend(random.sample(flat_remaining, min(len(flat_remaining), remaining_needed)))

        final_sample = sampled_diagrams + sampled_non_diagrams
        random.shuffle(final_sample)
        return final_sample

    def generate_review_dataset(self, sample: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formats sample questions into a clean structure of interest for review.
        """
        return [
            {
                "question_id": q.get("question_id"),
                "question": q.get("question"),
                "chapter": q.get("chapter"),
                "concept": q.get("concept"),
                "difficulty": q.get("difficulty"),
                "requires_diagram": q.get("requires_diagram"),
                "diagram_type": q.get("diagram_type", "none")
            }
            for q in sample
        ]
