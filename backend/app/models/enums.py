"""Shared literal type aliases used across request/response models and services."""

from typing import Literal

DifficultyLevel = Literal["easy", "medium", "hard"]

# Short, canonical question type codes used throughout the API.
# The raw dataset uses long-form names (e.g. "Very Short Answer (VSA)") which
# question_service normalizes into these codes on load.
QuestionType = Literal["MCQ", "VSA", "SA", "LA", "Case Study", "Assertion Reason"]

DiagramType = Literal["free_body", "circuit", "graph", "ray_diagram", "magnetic_field", "none"]

QuestionSource = Literal["pyq", "ai"]
