"""Loads the NCERT Physics Part-1 knowledge base and serves chapter content/excerpts.

The processed knowledge base lives under ``data/Book/chapters/*.json``, one
file per chapter, each containing the full chapter text plus metadata. This
service exposes that content in chunks small enough to ground Gemini prompts
without sending an entire chapter (10k-22k words) on every request.
"""

from __future__ import annotations

import json
import logging
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.core.exceptions import DataLoadError, ResourceNotFoundError

logger = logging.getLogger(__name__)

# NCERT section headings look like "3.1 INTRODUCTION" or "3.14 WHEATSTONE BRIDGE".
_SECTION_HEADING_RE = re.compile(r"^\d+\.\d+\s+[A-Z][A-Za-z .,\-\n]{3,}$", re.MULTILINE)

_STOPWORDS = {
    "a", "an", "and", "the", "of", "in", "on", "for", "to", "with", "is", "are",
    "due", "between", "its", "by", "from", "as", "at", "or", "their",
}


@dataclass(frozen=True)
class BookSection:
    """A titled section of a chapter (e.g. "3.14 WHEATSTONE BRIDGE")."""

    title: str
    text: str


@dataclass(frozen=True)
class BookChapter:
    """A single NCERT chapter loaded from the processed knowledge base."""

    chapter_number: int
    chapter_name: str
    content: str
    word_count: int
    sections: list[BookSection] = field(default_factory=list)


class BookService:
    """In-memory access layer over the NCERT Physics Part-1 knowledge base."""

    def __init__(self, chapters_dir: Path) -> None:
        self._chapters_dir = chapters_dir
        self._chapters: dict[str, BookChapter] = self._load(chapters_dir)
        logger.info(
            "BookService loaded %d NCERT chapters from %s",
            len(self._chapters),
            chapters_dir,
        )

    @staticmethod
    def _split_sections(content: str) -> list[BookSection]:
        matches = list(_SECTION_HEADING_RE.finditer(content))
        if len(matches) < 2:
            return []

        sections: list[BookSection] = []
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            title = " ".join(match.group().split())
            text = content[start:end].strip()
            if text:
                sections.append(BookSection(title=title, text=text))
        return sections

    @classmethod
    def _load(cls, chapters_dir: Path) -> dict[str, BookChapter]:
        if not chapters_dir.is_dir():
            raise DataLoadError(f"NCERT chapters directory not found: {chapters_dir}")

        chapters: dict[str, BookChapter] = {}
        for chapter_file in sorted(chapters_dir.glob("chapter_*.json")):
            try:
                raw = json.loads(chapter_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise DataLoadError(f"NCERT chapter file is not valid JSON: {chapter_file}") from exc

            chapter_name = raw["chapter_name"]
            content = raw.get("content", "")
            chapters[chapter_name] = BookChapter(
                chapter_number=raw.get("chapter_number", 0),
                chapter_name=chapter_name,
                content=content,
                word_count=raw.get("word_count", len(content.split())),
                sections=cls._split_sections(content),
            )
        return chapters

    def get_available_chapters(self) -> list[str]:
        """Return chapter names ordered by their NCERT chapter number."""

        return [c.chapter_name for c in sorted(self._chapters.values(), key=lambda c: c.chapter_number)]

    def get_chapter(self, chapter_name: str) -> BookChapter:
        """Return the full BookChapter for a given chapter name."""

        chapter = self._chapters.get(chapter_name)
        if chapter is None:
            raise ResourceNotFoundError(f"Chapter not found in NCERT knowledge base: {chapter_name}")
        return chapter

    def has_chapter(self, chapter_name: str) -> bool:
        """Whether NCERT content is available for the given chapter."""

        return chapter_name in self._chapters

    def get_chapter_content(self, chapter_name: str) -> str:
        """Return the full text content of a chapter."""

        return self.get_chapter(chapter_name).content

    def get_excerpt(
        self,
        chapter_name: str,
        concept: str | None = None,
        max_chars: int = 2500,
        rng: random.Random | None = None,
    ) -> str:
        """Return a grounding excerpt from a chapter, optionally targeted at a concept.

        If ``concept`` is provided, the section whose text best overlaps with
        the concept's keywords is returned. Otherwise a random section is
        chosen. Falls back to a slice of the raw content if the chapter has
        no detected section headings.
        """

        rng = rng or random
        chapter = self.get_chapter(chapter_name)

        if not chapter.sections:
            return chapter.content[:max_chars]

        section = None
        if concept:
            keywords = [w for w in re.findall(r"[a-zA-Z]+", concept.lower()) if w not in _STOPWORDS and len(w) > 2]
            if keywords:
                best_score = 0
                for candidate in chapter.sections:
                    haystack = candidate.text.lower()
                    score = sum(haystack.count(kw) for kw in keywords)
                    if score > best_score:
                        best_score = score
                        section = candidate

        if section is None:
            section = rng.choice(chapter.sections)

        excerpt = f"{section.title}\n{section.text}"
        return excerpt[:max_chars]
