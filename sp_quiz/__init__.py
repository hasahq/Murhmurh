#sp_quiz/__init__.py
"""
sp-quiz: Spaced Repetition Quiz Engine
spaced repetition engine designed to optimize long-term
memory retention through scientifically-backed review scheduling algorithms.


Basic Usage
    >>> from sp_quiz import Card, CardState, InMemoryStorage
    >>> storage = InMemoryStorage()
    >>> card = Card(
    ...     card_id="card_001",
    ...     user_id="user_123",
    ...     front="What is Python?",
    ...     back="A programming language"
    ... )
    >>> storage.save_card(card)


Features:
    - SM-2+ Algorithm: Enhanced SuperMemo 2 algorithm
    - Thread-Safe: Concurrent user support
    - Zero External Dependencies: Pure Python stdlib implementation
    - Flexible Storage: Abstract interface for various backends
    - PEP Compliant: Follows PEP 8, 257, 484
"""

from sp_quiz.__version__ import __version__

from sp_quiz.core import (
    Card,
    CardState,
    Review,
    UserProgress,
    SpQuizError,
    CardNotFoundError,
    InvalidCardStateError,
    SessionNotFoundError,
    SessionClosedError,
    InvalidQualityRatingError,
    StorageError,
    ConcurrencyError,
)

from sp_quiz.storage import (
    StorageInterface,
    InMemoryStorage
)

__all__ = [
    '__version__',
    'Card',
    'CardState',
    'Review',
    'UserProgress',
    'SpQuizError',
    'CardNotFoundError',
    'InvalidCardStateError',
    'SessionNotFoundError',
    'SessionClosedError',
    'InvalidQualityRatingError',
    'StorageError',
    'ConcurrencyError',
    'StorageInterface',
    'InMemoryStorage',
]

