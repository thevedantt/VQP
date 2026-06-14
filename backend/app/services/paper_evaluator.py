"""Automated quality scoring for generated papers (PART 8).

``PaperEvaluator.evaluate`` inspects an assembled ``GeneratedPaperResponse``
together with the inputs that produced it (the target chapter weightage and
the original request) and returns a ``QualityEvaluation`` with five 0-100
sub-scores plus a weighted ``overall_score``.
"""

from __future__ import annotations

from app.models.requests import GeneratePaperRequest
from app.models.responses import GeneratedPaperResponse, QualityEvaluation, QuestionItem
from app.services.question_service import TYPE_MARKS_MAP

_DIFFICULTY_LEVELS = ("easy", "medium", "hard")

# Weights for the overall_score weighted average. Chapter/diagram coverage and
# CBSE compliance are the structural correctness checks and are weighted
# highest; difficulty balance and question diversity are softer quality signals.
_OVERALL_WEIGHTS: dict[str, float] = {
    "chapter_coverage": 0.25,
    "diagram_coverage": 0.25,
    "cbse_compliance": 0.25,
    "difficulty_balance": 0.125,
    "question_diversity": 0.125,
}


class PaperEvaluator:
    """Computes automated quality scores for a generated paper."""

    def evaluate(
        self,
        paper: GeneratedPaperResponse,
        chapter_weightage: dict[str, int],
        request: GeneratePaperRequest,
    ) -> QualityEvaluation:
        all_questions = paper.questions + paper.generated_questions

        chapter_coverage = self._chapter_coverage(paper.chapter_distribution, chapter_weightage, len(all_questions))
        diagram_coverage = self._diagram_coverage(paper.diagram_coverage.diagram_percentage, request.diagram_percentage)
        difficulty_balance = self._difficulty_balance(all_questions)
        cbse_compliance = self._cbse_compliance(paper, all_questions)
        question_diversity = self._question_diversity(all_questions)

        scores = {
            "chapter_coverage": chapter_coverage,
            "diagram_coverage": diagram_coverage,
            "cbse_compliance": cbse_compliance,
            "difficulty_balance": difficulty_balance,
            "question_diversity": question_diversity,
        }
        overall_score = sum(scores[key] * weight for key, weight in _OVERALL_WEIGHTS.items())

        return QualityEvaluation(
            overall_score=round(overall_score, 1),
            cbse_compliance=round(cbse_compliance, 1),
            diagram_coverage=round(diagram_coverage, 1),
            chapter_coverage=round(chapter_coverage, 1),
            difficulty_balance=round(difficulty_balance, 1),
            question_diversity=round(question_diversity, 1),
        )

    @staticmethod
    def _chapter_coverage(chapter_distribution: dict[str, int], chapter_weightage: dict[str, int], total: int) -> float:
        if not chapter_weightage or total == 0:
            return 100.0

        deviations: list[float] = []
        for chapter, target_pct in chapter_weightage.items():
            actual_pct = chapter_distribution.get(chapter, 0) / total * 100
            deviations.append(abs(actual_pct - target_pct))

        mean_deviation = sum(deviations) / len(deviations)
        return max(0.0, min(100.0, 100.0 - mean_deviation))

    @staticmethod
    def _diagram_coverage(actual_pct: float, target_pct: int) -> float:
        deviation = abs(actual_pct - target_pct)
        return max(0.0, 100.0 - min(100.0, deviation * 2))

    @staticmethod
    def _difficulty_balance(questions: list[QuestionItem]) -> float:
        total = len(questions)
        if total == 0:
            return 0.0

        counts = {level: 0 for level in _DIFFICULTY_LEVELS}
        for question in questions:
            counts[question.difficulty] = counts.get(question.difficulty, 0) + 1

        distinct = sum(1 for count in counts.values() if count > 0)
        max_share = max(counts.values()) / total

        if distinct == 1:
            return 40.0
        if max_share <= 0.8:
            return 100.0

        overflow = max_share - 0.8
        return max(0.0, 100.0 - overflow / 0.2 * 60.0)

    @staticmethod
    def _cbse_compliance(paper: GeneratedPaperResponse, all_questions: list[QuestionItem]) -> float:
        checks: list[float] = []

        # 1. Every non-zero question type has at least one matching question
        #    placed in a section.
        types_in_sections: set[str] = set()
        for section in paper.sections:
            for question in section.questions:
                types_in_sections.add(question.type)

        active_types = [q_type for q_type, count in paper.type_distribution.items() if count > 0]
        if active_types:
            covered = sum(1 for q_type in active_types if q_type in types_in_sections)
            checks.append(covered / len(active_types) * 100)

        # 2. Each question's marks match its section's marks-per-question, and
        #    that value matches the canonical TYPE_MARKS_MAP for its type.
        marks_checks: list[bool] = []
        for section in paper.sections:
            for question in section.questions:
                expected = TYPE_MARKS_MAP.get(question.type, section.marks_per_question)
                marks_checks.append(question.marks == section.marks_per_question == expected)
        if marks_checks:
            checks.append(sum(marks_checks) / len(marks_checks) * 100)

        # 3. question_number sequence is exactly 1..N with no gaps/duplicates.
        if all_questions:
            numbers = sorted(q.question_number for q in all_questions)
            checks.append(100.0 if numbers == list(range(1, len(all_questions) + 1)) else 0.0)

        if not checks:
            return 0.0
        return sum(checks) / len(checks)

    @staticmethod
    def _question_diversity(questions: list[QuestionItem]) -> float:
        if not questions:
            return 0.0

        keys = {(question.concept or question.question[:60]) for question in questions}
        return len(keys) / len(questions) * 100
