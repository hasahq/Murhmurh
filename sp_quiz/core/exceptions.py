"""
Custom exceptions for the sp-quiz module.

This module defines the exception hierarchy used throughout the sp-quiz system.
All custom exceptions inherit from SpQuizError for easy catching and handling.

Exceptions:
    SpQuizError: Base exception for all sp-quiz errors
    CardNotFoundError: Raised when a card cannot be found
    InvalidCardStateError: Raised for invalid state transitions
    SessionNotFoundError: Raised when a session cannot be found
    SessionClosedError: Raised when operating on a closed session
    InvalidQualityRatingError: Raised for invalid quality ratings
    ReviewNotFoundError: Raised when a Review for a Card is non-discoverable
    ValidationError: Raised when there's Data Validation Error
    StorageError: Raised for storage operation failures
    ConcurrencyError: Raised for concurrent modification conflicts
"""


class SpQuizError(Exception):
    """Base exception for sp-quiz module."""
    pass


class CardNotFoundError(SpQuizError):
    """Card with given ID does not exist."""
    code = 'CARD_001'


class ReviewNotFoundError(SpQuizError):
    """Review with given ID does not exist"""
    code = 'REVIEW_002'


class ValidationError(SpQuizError):
    """Data validation failed."""
    code = 'VALIDATION_001'


class InvalidCardStateError(SpQuizError):
    """Invalid state transition requested."""
    code = 'CARD_002'


class SessionNotFoundError(SpQuizError):
    """Session with given ID does not exist."""
    code = 'SESSION_001'


class SessionClosedError(SpQuizError):
    """Operation on closed session."""
    code = 'SESSION_002'


class InvalidQualityRatingError(SpQuizError):
    """Quality rating must be 0-5."""
    code = 'REVIEW_001'


class StorageError(SpQuizError):
    """Storage operation failed."""
    code = 'STORAGE_001'


class ConcurrencyError(SpQuizError):
    """Concurrent modification detected."""
    code = 'CONCURRENCY_001'
