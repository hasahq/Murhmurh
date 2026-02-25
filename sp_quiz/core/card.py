"""
Card Data Model

Defines the Card dataclass and CardState enum used to represent
flashcards and their current state in the learning process.

Classes:
    CardState: Enum representing the different states a card can be in
    Card: Dataclass representing a flashcard with all associated metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional


class CardState(Enum):
    """
    Enum representing the different states a card can be in during learning.
    
    States:
        NEW: Card has never been reviewed
        LEARNING: Card is in the initial learning phase
        REVIEW: Card has graduated and is in long-term review
        RELEARNING: Card failed and needs to be relearned
        SUSPEND
    """
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    RELEARNING = "relearning"
    SUSPENDED = "suspended"



@dataclass
class Card:
    """
    Dataclass representing a flashcard in the spaced repetition system.
    
    A Card contains the question (front), answer (back), and all metadata
    required for spaced repetition scheduling including state, intervals,
    and learning statistics.
    
    Attributes:
        card_id: Unique identifier for the card
        user_id: ID of the user who owns this card
        front: Question or prompt text (front of card)
        back: Answer or explanation text (back of card)
        tags: List of tags for categorization
        metadata: Dictionary for additional custom metadata
        state: Current state of the card in the learning process
        due_datetime: When the card is next due for review
        interval_days: Current interval between reviews in days
        ease_factor: Multiplier for interval calculation (1.3-2.5)
        learning_step: Current step in the learning phase (0-based)
        reviews_count: Total number of times card has been reviewed
        lapses_count: Number of times card has been failed after graduating
        average_quality: Average quality rating across all reviews
        created_at: Timestamp when card was created
        updated_at: Timestamp when card was last modified
        last_reviewed_at: Timestamp of most recent review
    
    Raises:
        ValueError: If required fields are missing or empty
    """
    card_id: str
    user_id: str
    front: str
    back: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)
    state: CardState = CardState.NEW
    due_datetime: Optional[datetime] = None
    interval_days: float = 0.0
    ease_factor: float = 2.5
    learning_step: int = 0
    reviews_count: int = 0
    lapses_count: int = 0
    average_quality: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_reviewed_at: Optional[datetime] = None

    # Quality AutoScorer Fields
    global_review_count: int = 0
    global_mean_quality: int = 3.4
    global_success_rate: float = 0.65
    global_mean_first_time: float = 5.2
    difficulty_rating: float = 0.5 

    def __post_init__(self):
        """
        Validate card data after initialization.
        
        Raises:
            ValueError: If required fields are missing or empty
        """
        if not self.card_id or (isinstance(self.card_id, str) and not self.card_id.strip()):
            raise ValueError("card_id and user_id are required and cannot be empty")
        
        if not self.user_id or (isinstance(self.user_id, str) and not self.user_id.strip()):
            raise ValueError("card_id and user_id are required and cannot be empty")
        
        
        if not self.front or (isinstance(self.front, str) and not self.front.strip()):
            raise ValueError("front and back content are required and cannot be empty")
        
        if not self.back or (isinstance(self.back, str) and not self.back.strip()):
            raise ValueError("front and back content are required and cannot be empty")