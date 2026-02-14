"""
User progress data model.

This module defines the UserProgress dataclass used to track user statistics,
progress metrics, and learning analytics.

Classes:
    UserProgress: Dataclass representing a user's learning progress and statistics
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class UserProgress:
    """
    Dataclass representing a user's learning progress and statistics.
    
    UserProgress tracks comprehensive statistics about a user's learning
    including card counts, review statistics, streaks, velocity metrics,
    and retention rates.
    
    Attributes:
        user_id: Unique identifier for the user
        new_cards_count: Number of cards that have never been reviewed
        learning_cards_count: Number of cards in learning phase
        review_cards_count: Number of cards in review phase
        total_reviews: Total number of reviews performed by user
        reviews_today: Number of reviews done today
        successful_reviews: Number of successful reviews (quality >= 3)
        current_streak_days: Current consecutive days of reviews
        longest_streak_days: Longest streak of consecutive review days
        last_review_date: Date of the most recent review
        cards_added_last_7_days: Number of cards added in last 7 days
        cards_added_last_30_days: Number of cards added in last 30 days
        average_reviews_per_day: Average number of reviews per day
        retention_rate: Percentage of successful reviews
        difficulty_factor: User-specific difficulty adjustment factor
        created_at: Timestamp when user progress tracking started
        updated_at: Timestamp when progress was last updated
    
    Notes:
        - All count fields default to 0
        - Rates and factors default to appropriate base values
        - Timestamps are automatically managed
    """
    user_id: str
    new_cards_count: int = 0
    learning_cards_count: int = 0
    review_cards_count: int = 0
    total_reviews: int = 0
    reviews_today: int = 0
    successful_reviews: int = 0
    current_streak_days: int = 0
    longest_streak_days: int = 0
    last_review_date: Optional[datetime] = None
    cards_added_last_7_days: int = 0
    cards_added_last_30_days: int = 0
    average_reviews_per_day: float = 0.0
    retention_rate: float = 0.0
    difficulty_factor: float = 1.0
    created_at: datetime = field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.datetime.utcnow)
