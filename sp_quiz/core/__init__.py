# sp_quiz/core/__init__.py
"""
Core data models and exceptions for the sp-quiz spaced repetition engine.

Phase 1 exports: Card, CardState, Review, UserProgress, and the full
exception hierarchy.
"""

from sp_quiz.core.card import Card, CardState
from sp_quiz.core.exceptions import (
    CardNotFoundError,
    ConcurrencyError,
    InvalidCardStateError,
    InvalidQualityRatingError,
    SessionClosedError,
    SessionNotFoundError,
    SpQuizError,
    StorageError,
)
from sp_quiz.core.review import Review
from sp_quiz.core.user import UserProgress

__all__ = [
    # Card
    "Card",
    "CardState",
    # Review
    "Review",
    # User
    "UserProgress",
    # Exceptions
    "SpQuizError",
    "CardNotFoundError",
    "InvalidCardStateError",
    "SessionNotFoundError",
    "SessionClosedError",
    "InvalidQualityRatingError",
    "StorageError",
    "ConcurrencyError",
]