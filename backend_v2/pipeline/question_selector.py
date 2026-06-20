"""
Quota-driven question selection - Paper Generation Engine (Phase 3B).

Diagram generation is explicitly out of scope. The classifier /
schema_router / blueprint_generator / blueprint_evaluator /
compiler_router stack is NOT imported here - diagram_detector.py is a
keyword heuristic, detection only, never generation.

For every (section, block) in a template:
    1. Fill the block's diagram quota first, PYQ candidates first, in
       stable dataset order (least-used chapter first - Task 4), using
       their known diagram_required flag; AI is used as a
       diagram-required fallback if the PYQ pool can't satisfy the
       quota for that question type.
    2. Fill the remaining slots honoring the PYQ/AI ratio, same
       chapter-balanced ordering.
    3. Avoid duplicate PYQ reuse, duplicate question text, and repeated
       concepts (Task 2) - a concept used anywhere earlier in the paper
       is not reused, UNLESS no concept-fresh candidate exists and a
       quota would otherwise go unfilled, in which case a concept
       repeat is allowed as a last resort before falling back to AI.

After every block is filled, enforce_overall_diagram_ratio() does a
paper-wide top-up pass so the whole paper hits the 20-30% diagram
coverage target, since per-block quotas alone don't guarantee it.

Selection is deliberate and quota-driven throughout - PYQ candidates
are walked in stable dataset order (chapter-balanced), never shuffled,
so results are reproducible.
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
BACKEND_V2 = PIPELINE_DIR.parent

sys.path.insert(0, str(BACKEND_V2))

from pipeline.ai_question_generator import AIQuestionGenerator
from pipeline.diagram_detector import detect_diagram_family, detect_diagram_required
from pipeline.normalize_unicode import normalize


DESCRIPTIVE_DATASET_PATH = BACKEND_V2 / "data" / "descriptive_questions.json"
MCQ_DATASET_PATH = BACKEND_V2 / "data" / "mcq_questions.json"

_pyq_pool = None


def _load_pyq_pool():
    global _pyq_pool
    if _pyq_pool is None:
        pool = []
        for path in (DESCRIPTIVE_DATASET_PATH, MCQ_DATASET_PATH):
            with open(path, "r", encoding="utf-8") as f:
                pool.extend(json.load(f))

        for q in pool:
            # Defense-in-depth: the datasets are already normalized at
            # build time, but re-running normalize() here is a cheap
            # no-op on clean text and protects against future raw
            # additions to the JSON files (Task 1).
            q["question"] = normalize(q.get("question") or "")
            if q.get("options"):
                q["options"] = {k: normalize(str(v)) for k, v in q["options"].items()}

            if q.get("diagram_required") is None:
                detected = detect_diagram_required(q["question"])
                q["diagram_required"] = detected
                print(f"[DIAGRAM DETECTION] {q.get('pyq_id')}: flag missing, heuristic -> {detected}")

            q["diagram_family"] = detect_diagram_family(q["question"]) if q["diagram_required"] else None

        _pyq_pool = pool
    return _pyq_pool


def _normalize_text(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


class QuestionSelector:

    def __init__(self, pyq_ratio=60, ai_ratio=40, chapter_filters=None, difficulty=None, logger=None):
        total_ratio = pyq_ratio + ai_ratio
        if total_ratio <= 0:
            raise ValueError("pyq_ratio + ai_ratio must be > 0")

        self.pyq_ratio = pyq_ratio / total_ratio
        self.ai_ratio = ai_ratio / total_ratio
        self.chapter_filters = chapter_filters
        self.difficulty = difficulty
        self.logger = logger

        self.ai_generator = AIQuestionGenerator()
        self.used_pyq_ids = set()
        self.used_texts = set()
        self.used_concepts = set()
        self.chapter_usage = Counter()  # Task 4: section/chapter balancing

    # ---- internal helpers -------------------------------------------------

    def _pyq_candidates(self, qtype, allow_concept_repeat=False):
        pool = _load_pyq_pool()
        candidates = []
        for q in pool:
            if q["type"] != qtype:
                continue
            if q["pyq_id"] in self.used_pyq_ids:
                continue
            if _normalize_text(q["question"]) in self.used_texts:
                continue
            if not allow_concept_repeat and q.get("concept") and q["concept"] in self.used_concepts:
                continue
            if self.chapter_filters and q.get("chapter") and q["chapter"] not in self.chapter_filters:
                continue
            if self.difficulty and q.get("difficulty") and q["difficulty"] != self.difficulty:
                continue
            candidates.append(q)

        # Task 4: prefer the least-used chapter so far in this paper,
        # so one block doesn't pull 5 questions from the same chapter.
        # Stable sort keeps dataset order among equally-used chapters.
        candidates.sort(key=lambda c: self.chapter_usage.get(c.get("chapter"), 0))
        return candidates

    def _take_pyq(self, candidate):
        self.used_pyq_ids.add(candidate["pyq_id"])
        self.used_texts.add(_normalize_text(candidate["question"]))
        if candidate.get("concept"):
            self.used_concepts.add(candidate["concept"])
        self.chapter_usage[candidate.get("chapter")] += 1

    def _take_text(self, text, chapter=None):
        self.used_texts.add(_normalize_text(text))
        self.chapter_usage[chapter] += 1

    @staticmethod
    def _row(source, qtype, marks, section_id, text, options=None,
             diagram_required=False, diagram_family=None, pyq_id=None,
             chapter=None, concept=None):
        return {
            "question_id": None,
            "section_id": section_id,
            "type": qtype,
            "marks": marks,
            "source": source,
            "pyq_id": pyq_id,
            "question": text,
            "options": options,
            "diagram_required": bool(diagram_required),
            "diagram_family": diagram_family,
            "chapter": chapter,
            "concept": concept,
        }

    def _generate_ai_question(self, qtype, marks, require_diagram):
        avoid_topics = list(self.used_concepts) + list(self.used_texts)
        ai_q = self.ai_generator.generate(
            qtype, marks,
            require_diagram=require_diagram,
            difficulty=self.difficulty,
            avoid_topics=avoid_topics,
        )
        ai_q["question"] = normalize(ai_q["question"])
        ai_q["diagram_family"] = (
            detect_diagram_family(ai_q["question"]) if ai_q.get("diagram_required") else None
        )
        return ai_q

    def _pyq_candidates_with_fallback(self, qtype):
        """Strict (no concept repeat) candidates, then concept-repeat
        candidates appended as a last-resort tail (Task 2's "unless
        required" rule)."""
        strict = self._pyq_candidates(qtype, allow_concept_repeat=False)
        strict_ids = {c["pyq_id"] for c in strict}
        relaxed = [
            c for c in self._pyq_candidates(qtype, allow_concept_repeat=True)
            if c["pyq_id"] not in strict_ids
        ]
        return strict + relaxed

    # ---- per-block selection ------------------------------------------------

    def select_for_block(self, section_id, qtype, count, marks_each, diagram_quota=None):
        diagram_quota = diagram_quota or {}
        is_hard_quota = "min" in diagram_quota
        diagram_min = diagram_quota.get("min") or diagram_quota.get("prefer") or 0

        selected = []
        diagram_filled = 0
        target_pyq_count = round(count * self.pyq_ratio)

        # ---- Step 1: fill diagram quota first, PYQ first ----
        if diagram_min > 0:
            for cand in self._pyq_candidates_with_fallback(qtype):
                if diagram_filled >= diagram_min or len(selected) >= count:
                    break
                if cand.get("diagram_required"):
                    self._take_pyq(cand)
                    selected.append(self._row(
                        "PYQ", qtype, marks_each, section_id, cand["question"],
                        options=cand.get("options"),
                        diagram_required=True,
                        diagram_family=cand.get("diagram_family"),
                        pyq_id=cand["pyq_id"],
                        chapter=cand.get("chapter"),
                        concept=cand.get("concept"),
                    ))
                    diagram_filled += 1

            attempts = 0
            while diagram_filled < diagram_min and len(selected) < count and attempts < diagram_min + 2:
                attempts += 1
                try:
                    ai_q = self._generate_ai_question(qtype, marks_each, require_diagram=True)
                except Exception as e:
                    if self.logger:
                        self.logger.log_error("AI QUESTION GENERATOR", str(e))
                    continue

                if _normalize_text(ai_q["question"]) in self.used_texts:
                    continue

                self._take_text(ai_q["question"])
                selected.append(self._row(
                    "AI", qtype, marks_each, section_id, ai_q["question"],
                    options=ai_q.get("options"),
                    diagram_required=True,
                    diagram_family=ai_q.get("diagram_family"),
                ))
                diagram_filled += 1

                if not is_hard_quota:
                    break  # "prefer" quota: one good-faith attempt is enough

            if diagram_filled < diagram_min and self.logger:
                self.logger.log_error(
                    "DIAGRAM QUOTA",
                    f"Section {section_id} ({qtype}): wanted {diagram_min} diagram "
                    f"question(s), only filled {diagram_filled}",
                )

        # ---- Step 2: fill remaining slots, honoring the PYQ/AI ratio ----
        pyq_used_so_far = sum(1 for r in selected if r["source"] == "PYQ")
        remaining_pyq_target = max(0, target_pyq_count - pyq_used_so_far)

        for cand in self._pyq_candidates_with_fallback(qtype):
            if len(selected) >= count or remaining_pyq_target <= 0:
                break
            self._take_pyq(cand)
            selected.append(self._row(
                "PYQ", qtype, marks_each, section_id, cand["question"],
                options=cand.get("options"),
                diagram_required=cand.get("diagram_required", False),
                diagram_family=cand.get("diagram_family"),
                pyq_id=cand["pyq_id"],
                chapter=cand.get("chapter"),
                concept=cand.get("concept"),
            ))
            remaining_pyq_target -= 1

        attempts = 0
        while len(selected) < count and attempts < count * 3:
            attempts += 1
            try:
                ai_q = self._generate_ai_question(qtype, marks_each, require_diagram=False)
            except Exception as e:
                if self.logger:
                    self.logger.log_error("AI QUESTION GENERATOR", str(e))
                continue

            if _normalize_text(ai_q["question"]) in self.used_texts:
                continue

            self._take_text(ai_q["question"])
            selected.append(self._row(
                "AI", qtype, marks_each, section_id, ai_q["question"],
                options=ai_q.get("options"),
                diagram_required=ai_q.get("diagram_required", False),
                diagram_family=ai_q.get("diagram_family"),
            ))

        if len(selected) < count and self.logger:
            self.logger.log_error(
                "QUESTION SELECTOR",
                f"Section {section_id} ({qtype}): wanted {count} question(s), "
                f"only filled {len(selected)}",
            )

        return selected

    def select_for_template(self, template):
        rows = []
        for section in template["sections"]:
            for block in section["blocks"]:
                rows.extend(self.select_for_block(
                    section_id=section["section_id"],
                    qtype=block["type"],
                    count=block["count"],
                    marks_each=block["marks_each"],
                    diagram_quota=block.get("diagram_quota"),
                ))
        return rows

    # ---- paper-wide diagram coverage enforcement ----------------------------

    def enforce_overall_diagram_ratio(self, rows, target_ratio=0.2):
        total = len(rows)
        if total == 0:
            return rows

        needed = math.ceil(target_ratio * total)
        diagram_count = sum(1 for r in rows if r.get("diagram_required"))

        if diagram_count >= needed:
            return rows

        non_diagram_idx = [i for i, r in enumerate(rows) if not r.get("diagram_required")]
        non_diagram_idx.sort(key=lambda i: 0 if rows[i]["source"] == "AI" else 1)

        for i in non_diagram_idx:
            if diagram_count >= needed:
                break
            row = rows[i]

            if row["source"] == "AI":
                try:
                    ai_q = self._generate_ai_question(row["type"], row["marks"], require_diagram=True)
                except Exception as e:
                    if self.logger:
                        self.logger.log_error("DIAGRAM TOP-UP", str(e))
                    continue

                if _normalize_text(ai_q["question"]) in self.used_texts:
                    continue

                self.used_texts.discard(_normalize_text(row["question"]))
                self._take_text(ai_q["question"])
                row.update({
                    "question": ai_q["question"],
                    "options": ai_q.get("options"),
                    "diagram_required": True,
                    "diagram_family": ai_q.get("diagram_family"),
                })
                diagram_count += 1

            else:
                for cand in self._pyq_candidates_with_fallback(row["type"]):
                    if cand.get("diagram_required"):
                        self.used_pyq_ids.discard(row.get("pyq_id"))
                        self.used_texts.discard(_normalize_text(row["question"]))
                        self._take_pyq(cand)
                        row.update({
                            "pyq_id": cand["pyq_id"],
                            "question": cand["question"],
                            "options": cand.get("options"),
                            "diagram_required": True,
                            "diagram_family": cand.get("diagram_family"),
                            "chapter": cand.get("chapter"),
                            "concept": cand.get("concept"),
                        })
                        diagram_count += 1
                        break

        if diagram_count < needed and self.logger:
            self.logger.log_error(
                "DIAGRAM QUOTA",
                f"Overall diagram coverage target not met: {diagram_count}/{total} "
                f"(< {needed} needed for {int(target_ratio * 100)}%)",
            )

        return rows

    # ---- paper-wide PYQ/AI ratio enforcement -------------------------------
    #
    # Per-block selection (select_for_block) only targets a per-block PYQ
    # count, which drifts from the paper-wide configured ratio: rounding
    # per block doesn't sum back to round(total * ratio), and a block's
    # diagram_quota can force an AI fallback that silently eats a slot the
    # ratio expected to be PYQ. This pass recomputes the quota from the
    # FINAL total question count and corrects the actual paper by swapping
    # AI<->PYQ rows until the exact quota is met, before the paper is
    # finalized - never just relabeling percentages after the fact.

    def compute_pyq_quota(self, total_questions):
        """Paper-wide PYQ/AI quota, calculated from the configured ratio
        BEFORE any percentage is derived from the actual selection."""
        pyq_quota = round(total_questions * self.pyq_ratio)
        ai_quota = total_questions - pyq_quota
        return pyq_quota, ai_quota

    def _swap_one_ai_to_pyq(self, rows):
        """Replace one AI row with a same-type PYQ candidate. Prefers a
        non-diagram-required AI row so existing diagram quotas aren't
        disturbed. Returns True if a swap was made."""
        ai_rows = sorted(
            (r for r in rows if r["source"] == "AI"),
            key=lambda r: r.get("diagram_required", False),
        )

        for row in ai_rows:
            for cand in self._pyq_candidates_with_fallback(row["type"]):
                if row.get("diagram_required") and not cand.get("diagram_required"):
                    continue  # would break this row's diagram quota
                self.used_texts.discard(_normalize_text(row["question"]))
                self._take_pyq(cand)
                row.update({
                    "source": "PYQ",
                    "pyq_id": cand["pyq_id"],
                    "question": cand["question"],
                    "options": cand.get("options"),
                    "diagram_required": cand.get("diagram_required", False),
                    "diagram_family": cand.get("diagram_family"),
                    "chapter": cand.get("chapter"),
                    "concept": cand.get("concept"),
                })
                return True
        return False

    def _swap_one_pyq_to_ai(self, rows):
        """Replace one PYQ row with a freshly generated AI question of the
        same type/marks. Prefers a non-diagram-required PYQ row so existing
        diagram quotas aren't disturbed. Returns True if a swap was made."""
        pyq_rows = sorted(
            (r for r in rows if r["source"] == "PYQ"),
            key=lambda r: r.get("diagram_required", False),
        )

        for row in pyq_rows:
            try:
                ai_q = self._generate_ai_question(
                    row["type"], row["marks"],
                    require_diagram=row.get("diagram_required", False),
                )
            except Exception as e:
                if self.logger:
                    self.logger.log_error("PYQ/AI RATIO SWAP", str(e))
                continue

            if _normalize_text(ai_q["question"]) in self.used_texts:
                continue

            self.used_pyq_ids.discard(row.get("pyq_id"))
            self.used_texts.discard(_normalize_text(row["question"]))
            self._take_text(ai_q["question"])
            row.update({
                "source": "AI",
                "pyq_id": None,
                "question": ai_q["question"],
                "options": ai_q.get("options"),
                "diagram_required": ai_q.get("diagram_required", False),
                "diagram_family": ai_q.get("diagram_family"),
            })
            return True
        return False

    def enforce_overall_pyq_ratio(self, rows):
        """
        Final correction pass (Phase: PYQ/AI split accuracy fix): swap
        AI<->PYQ rows until the actual paper-wide PYQ/AI counts exactly
        match the configured ratio's quota. Raises AssertionError if the
        dataset/AI generation can't satisfy the quota even after
        exhausting reasonable swap attempts - a paper that silently
        ships the wrong split is worse than a loud, clear failure.
        """
        total = len(rows)
        if total == 0:
            return rows

        pyq_quota, ai_quota = self.compute_pyq_quota(total)
        max_attempts = total * 3

        for _ in range(max_attempts):
            pyq_count = sum(1 for r in rows if r["source"] == "PYQ")
            if pyq_count == pyq_quota:
                break
            if pyq_count < pyq_quota:
                if not self._swap_one_ai_to_pyq(rows):
                    break
            else:
                if not self._swap_one_pyq_to_ai(rows):
                    break

        pyq_count = sum(1 for r in rows if r["source"] == "PYQ")
        ai_count = total - pyq_count

        if pyq_count != pyq_quota or ai_count != ai_quota:
            message = (
                f"PYQ/AI quota not satisfied after exhausting sampling attempts: "
                f"pyq={pyq_count} (target {pyq_quota}), ai={ai_count} (target {ai_quota})"
            )
            if self.logger:
                self.logger.log_error("PYQ/AI RATIO", message)
            assert pyq_count == pyq_quota, message
            assert ai_count == ai_quota, message

        return rows
