"""
Storage implementations for sp-quiz persistence layer.

This package contains the abstract storage interface and concrete
implementations for data persistence including in-memory storage.
"""

from sp_quiz.storage.interface import StorageInterface
from sp_quiz.storage.memory import InMemoryStorage

__all__ = [
    'StorageInterface',
    'InMemoryStorage',
]