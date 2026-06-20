"""Diagram Retrieval Service (V1).

Loads the local diagram library (JSON files), classifies a physics question
into a renderer_type/concept/scenario, selects the matching library file,
and retrieves the most similar schema via TF-IDF cosine similarity.

No vector database, no FAISS, no Pinecone, no RAG framework.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.exceptions import DataLoadError

logger = logging.getLogger(__name__)

# Map renderer_type to library filename.
_RENDERER_TO_FILE: dict[str, str] = {
    "ray_optics": "ray.json",
    "circuit": "circuit.json",
    "magnetic_field": "magnetic.json",
    "graph": "graph.json",
    "free_body": "fbd.json",
}

# Map DiagramService diagram_type -> renderer_type.
_DIAGRAM_TYPE_TO_RENDERER: dict[str, str] = {
    "ray_diagram": "ray_optics",
    "circuit": "circuit",
    "magnetic_field": "magnetic_field",
    "graph": "graph",
    "free_body": "free_body",
}

# Explicit diagram name phrases → renderer_type (same priority order as DiagramService).
_EXPLICIT_RENDERER_PATTERNS: list[tuple[str, list[str]]] = [
    ("ray_optics", ["ray diagram"]),
    ("circuit", ["circuit diagram"]),
    ("free_body", ["free body diagram", "free-body diagram"]),
    ("magnetic_field", ["magnetic field lines", "field lines"]),
]

# Topical keyword sets → renderer_type.
_TOPIC_RENDERER_KEYWORDS: list[tuple[str, list[str]]] = [
    (
        "circuit",
        [
            "wheatstone bridge", "meter bridge", "potentiometer",
            "ammeter", "voltmeter", "galvanometer",
            "given circuit", "the circuit", "resistors are connected",
            "cells are connected", "kirchhoff",
        ],
    ),
    (
        "ray_optics",
        [
            "convex lens", "concave lens", "convex mirror", "concave mirror",
            "plane mirror", "compound microscope", "telescope",
            "magnifying power", "refraction through", "image formed by", "prism",
        ],
    ),
    (
        "magnetic_field",
        [
            "magnetic field due to", "magnetic field at", "solenoid", "toroid",
            "current carrying conductor", "current-carrying conductor", "current loop",
        ],
    ),
    (
        "free_body",
        [
            "free body", "forces acting on", "block of mass",
            "inclined plane", "tension in the string", "normal reaction",
        ],
    ),
    (
        "graph",
        [
            "draw the graph", "draw a graph", "plot a graph", "plot the graph",
            "sketch the graph", "graph showing the variation", "graph between",
        ],
    ),
]

# Concept name -> categorical lens/mirror type for extra hints.
_LENS_TYPES: dict[str, str] = {"convex_lens": "convex", "concave_lens": "concave"}
_MIRROR_TYPES: dict[str, str] = {"concave_mirror": "concave", "convex_mirror": "convex", "plane_mirror": "plane"}
_MAGNETIC_VIEWING_PLANE: dict[str, str] = {
    "solenoid": "axial", "toroid": "axial", "circular_loop": "axial",
    "straight_wire": "cross_section", "bar_magnet": "side",
}
_MAGNETIC_DEFAULT_DIRECTION: dict[str, str] = {
    "solenoid": "anticlockwise", "toroid": "anticlockwise",
    "circular_loop": "anticlockwise", "straight_wire": "out_of_page",
}
_DIRECTION_PHRASES: list[tuple[str, str]] = [
    ("anticlockwise", "anticlockwise"), ("counterclockwise", "anticlockwise"),
    ("clockwise", "clockwise"), ("into the page", "into_page"),
    ("into the plane", "into_page"), ("into page", "into_page"),
    ("out of the page", "out_of_page"), ("out of the plane", "out_of_page"),
    ("out of page", "out_of_page"),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _detect_current_direction(question_text: str) -> str | None:
    text = question_text.lower()
    for phrase, direction in _DIRECTION_PHRASES:
        if phrase in text:
            return direction
    return None


class DiagramRetrievalService:
    """Loads the diagram library and provides classify + retrieve operations."""

    def __init__(self, library_dir: Path) -> None:
        self._library: dict[str, list[dict[str, Any]]] = {}
        self._tfidf_vectors: dict[str, tuple[TfidfVectorizer, np.ndarray]] = {}
        self._load_library(library_dir)

    def _load_library(self, library_dir: Path) -> None:
        if not library_dir.is_dir():
            raise DataLoadError(f"Diagram library directory not found: {library_dir}")

        for filename in _RENDERER_TO_FILE.values():
            filepath = library_dir / filename
            if not filepath.exists():
                logger.warning("Library file not found: %s", filepath)
                self._library[filename] = []
                continue
            try:
                raw = json.loads(filepath.read_text(encoding="utf-8"))
                self._library[filename] = raw if isinstance(raw, list) else [raw]
            except (json.JSONDecodeError, OSError) as exc:
                raise DataLoadError(f"Failed to load library file {filepath}: {exc}") from exc

        # Pre-build TF-IDF vectors for each file.
        for filename, entries in self._library.items():
            if not entries:
                self._tfidf_vectors[filename] = (TfidfVectorizer(), np.empty((0, 0)))
                continue
            corpus = [self._build_search_text(e) for e in entries]
            vectorizer = TfidfVectorizer(stop_words="english")
            vectors = vectorizer.fit_transform(corpus)
            self._tfidf_vectors[filename] = (vectorizer, vectors)

        logger.info(
            "DiagramRetrievalService loaded %d library files from %s",
            len(self._library),
            library_dir,
        )

    @staticmethod
    def _build_search_text(entry: dict[str, Any]) -> str:
        parts = [
            entry.get("concept", ""),
            entry.get("scenario", ""),
            entry.get("diagram_family", ""),
            entry.get("diagram_subtype", ""),
            entry.get("diagram_description", ""),
        ]
        return " ".join(p.strip() for p in parts if p.strip())

    # ------------------------------------------------------------------
    # Step 2: Classify Question
    # ------------------------------------------------------------------
    def classify(self, question_text: str) -> dict[str, str]:
        """Return ``{"renderer_type": ..., "concept": ..., "scenario": ...}``."""
        renderer_type = self._detect_renderer_type(question_text)
        concept, scenario = self._infer_concept_scenario(question_text, renderer_type)
        return {
            "renderer_type": renderer_type,
            "concept": concept,
            "scenario": scenario,
        }

    def _detect_renderer_type(self, question_text: str) -> str:
        text = _normalize(question_text)

        for renderer_type, phrases in _EXPLICIT_RENDERER_PATTERNS:
            for phrase in phrases:
                if phrase in text:
                    return renderer_type

        for renderer_type, keywords in _TOPIC_RENDERER_KEYWORDS:
            if any(kw in text for kw in keywords):
                return renderer_type

        return "graph"

    def _infer_concept_scenario(self, question_text: str, renderer_type: str) -> tuple[str, str]:
        filename = _RENDERER_TO_FILE.get(renderer_type)
        if not filename:
            return "generic", "generic"

        entries = self._library.get(filename, [])
        if not entries:
            return "generic", "generic"

        text = _normalize(question_text)
        vectorizer, vectors = self._tfidf_vectors[filename]

        if vectors.shape[0] == 0:
            return "generic", "generic"

        query_vec = vectorizer.transform([text])
        scores = cosine_similarity(query_vec, vectors).flatten()
        best_idx = int(np.argmax(scores))

        entry = entries[best_idx]
        concept = entry.get("concept", "generic")
        scenario = entry.get("scenario", "generic")

        # If best match has very low score, fall back.
        if scores[best_idx] < 0.05:
            concept = "generic"
            scenario = "generic"

        return concept, scenario

    # ------------------------------------------------------------------
    # Step 3: Select Library File
    # ------------------------------------------------------------------
    def select_library_file(self, renderer_type: str) -> str:
        """Return the filename for the given renderer_type."""
        return _RENDERER_TO_FILE.get(renderer_type, "graph.json")

    # ------------------------------------------------------------------
    # Step 4: Similarity Search
    # ------------------------------------------------------------------
    def retrieve(self, question_text: str, renderer_type: str) -> dict[str, Any] | None:
        """Return the top-matching schema from the library for the given renderer_type."""
        filename = self.select_library_file(renderer_type)
        entries = self._library.get(filename, [])
        if not entries:
            return None

        text = _normalize(question_text)
        vectorizer, vectors = self._tfidf_vectors[filename]

        if vectors.shape[0] == 0:
            return entries[0]

        query_vec = vectorizer.transform([text])
        scores = cosine_similarity(query_vec, vectors).flatten()
        best_idx = int(np.argmax(scores))

        if scores[best_idx] < 0.01:
            return entries[0]

        entry = entries[best_idx]
        logger.info(
            "Retrieved schema for renderer_type=%s, concept=%s, scenario=%s, score=%.3f",
            renderer_type,
            entry.get("concept"),
            entry.get("scenario"),
            scores[best_idx],
        )
        return entry

    def retrieve_similarity_details(
        self, question_text: str, renderer_type: str
    ) -> tuple[dict[str, Any] | None, float, str]:
        """Returns (schema, score, matched_text) for debugging."""
        filename = self.select_library_file(renderer_type)
        entries = self._library.get(filename, [])
        if not entries:
            return None, 0.0, ""

        text = _normalize(question_text)
        vectorizer, vectors = self._tfidf_vectors[filename]

        if vectors.shape[0] == 0:
            return entries[0], 0.0, ""

        query_vec = vectorizer.transform([text])
        scores = cosine_similarity(query_vec, vectors).flatten()
        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])
        entry = entries[best_idx]
        matched_text = self._build_search_text(entry)
        return entry, best_score, matched_text
