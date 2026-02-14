"""
Review data model for spaced repetition system.

This module defines the Review dataclass used to record review sessions
and their outcomes, including quality ratings and state transitions.

Classes:
    Review: Dataclass representing a single card review event
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sp_quiz.core.card import CardState


@dataclass
class Review:
    """
    Dataclass representing a single review of a flashcard.
    
    A Review captures all information about a card review event, including
    the quality rating, time taken, and the before/after state of the card
    for tracking learning progress.
    
    Attributes:
        review_id: Unique identifier for this review
        card_id: ID of the card being reviewed
        user_id: ID of the user performing the review
        session_id: ID of the review session this belongs to
        quality: Quality rating from 0-5 indicating recall difficulty
        time_taken_seconds: Time spent on this review in seconds
        state_before: Card state before this review
        interval_before: Interval in days before this review
        ease_factor_before: Ease factor before this review
        state_after: Card state after this review
        interval_after: Interval in days after this review
        ease_factor_after: Ease factor after this review
        due_datetime_after: Next due datetime after this review
        reviewed_at: Timestamp when this review occurred
    
    Raises:
        ValueError: If quality is not 0-5 or time is negative
    """
    review_id: str
    card_id: str
    user_id: str
    session_id: str
    quality: int[Optional]
    time_taken_seconds: float
    state_before: CardState
    interval_before: float
    ease_factor_before: float
    state_after: CardState
    interval_after: float
    ease_factor_after: float
    due_datetime_after: datetime
    reviewed_at: datetime = field(default_factory=datetime.datetime.utcnow)
    
    def __post_init__(self):
        """
        Validate review data after initialization.
        
        Raises:
            ValueError: If quality is not 0-5 or time is negative
        """
        if self.quality:
            if not (0 <= self.quality <= 5):
                raise ValueError("quality must be between 0 and 5")
        
        if self.time_taken_seconds < 0:
            raise ValueError("time_taken_seconds must be non-negative")
