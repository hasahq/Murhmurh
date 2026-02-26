"""
SM-2+ Spaced Repetition Algorithm

Enhanced SuperMemo 2 algorithm with adaptive difficulty adjustments.
Calculates optimal review intervals based on user performance.

Classes:
    ScheduleUpdate: Result of interval calculation
    SM2Plus: Main algorithm implementation

Constants:
    MIN_EF: Minimum ease factor (1.3)
    MAX_EF: Maximum ease factor (2.5)
    MIN_INTERVAL: Minimum interval in days
    MAX_INTERVAL: Maximum interval in days (365 days)
    LEARNING_STEPS: Learning phase step intervals
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..core.card import Card, CardState
from .utils import (
    clamp, ease_factor_delta, calculate_interval,
    MIN_INTERVAL_DAYS, MAX_INTERVAL_DAYS
)

# Algorithm constants
MIN_EF = 1.3
MAX_EF = 2.5
MIN_INTERVAL = MIN_INTERVAL_DAYS
MAX_INTERVAL = MAX_INTERVAL_DAYS

# Learning phase step intervals (in seconds)
LEARNING_STEPS = [
    60,      # Step 0->1: 1 minute
    600,     # Step 1->2: 10 minutes
    86400    # Step 2->graduation: 1 day
]


@dataclass
class ScheduleUpdate:
    """
    Result of SM-2+ interval calculation.
    
    Contains all information needed to update a card's scheduling state
    after a review.
    
    Attributes:
        interval_days: Next interval in days
        new_ease_factor: Updated ease factor
        new_state: Updated card state
        new_learning_step: Updated learning step (0 if graduated)
        new_lapses_count: Updated lapse counter
        next_due: Datetime when card is next due
    """
    interval_days: float
    new_ease_factor: float
    new_state: CardState
    new_learning_step: int
    new_lapses_count: int
    next_due: datetime


class SM2Plus:
    """
    Enhanced SM-2 algorithm implementation.
    
    Implements spaced repetition scheduling with:
    - Learning phase progression (3 steps)
    - Ease factor adjustments based on quality
    - Lapse handling with relearning
    - Adaptive difficulty factors
    - Interval clamping and bounds checking
    
    Methods:
        calculate_next_interval: Main scheduling calculation
        adjust_ease_factor: Update ease factor based on quality
        handle_lapse: Handle failed reviews
        calculate_initial_interval: First review interval
        calculate_difficulty_factor: User-specific difficulty adjustment
    """
    
    def __init__(self):
        """Initialize SM-2+ algorithm."""
        pass
    
    def calculate_next_interval(self, card: Card, quality: int,
                               difficulty_factor: float = 1.0) -> ScheduleUpdate:
        """
        Calculate next review interval based on card state and quality.
        
        This is the main entry point for the SM-2+ algorithm.
        
        Args:
            card: Card object with current state
            quality: Quality rating 0-5
                0 = Complete blackout
                1 = Incorrect, barely familiar
                2 = Incorrect but familiar
                3 = Correct with difficulty
                4 = Correct after hesitation
                5 = Perfect recall
            difficulty_factor: User-specific difficulty multiplier (0.7-1.3)
        
        Returns:
            ScheduleUpdate with new scheduling parameters
        
        Algorithm Flow:
            1. NEW/LEARNING cards: Progress through learning steps
            2. REVIEW cards with q≥3: Increase interval
            3. REVIEW cards with q<3: Handle as lapse
            4. Apply EF adjustments and clamping
        """
        # Validate quality
        if not (0 <= quality <= 5):
            raise ValueError(f"Quality must be 0-5, got {quality}")
        
        # Handle learning phase
        if card.state in (CardState.NEW, CardState.LEARNING):
            return self._handle_learning_phase(card, quality)
        
        # Handle relearning phase
        if card.state == CardState.RELEARNING:
            return self._handle_relearning_phase(card, quality)
        
        # Handle review phase
        if card.state == CardState.REVIEW:
            # Check for lapse
            if quality < 3:
                return self._handle_review_lapse(card)
            else:
                return self._handle_review_success(card, quality, difficulty_factor)
        
        # Fallback (should not reach here)
        raise ValueError(f"Unsupported card state: {card.state}")
    
    def _handle_learning_phase(self, card: Card, quality: int) -> ScheduleUpdate:
        """Handle NEW and LEARNING state cards."""
        current_step = card.learning_step if card.state == CardState.LEARNING else 0
        
        # Check if we should advance
        if quality >= 3:
            next_step = current_step + 1
            
            # Check for graduation
            if next_step >= len(LEARNING_STEPS):
                # Graduate to review phase with 1-day interval
                new_ef = self.adjust_ease_factor(card.ease_factor, quality)
                interval_days = 1.0
                next_due = datetime.utcnow() + timedelta(days=interval_days)
                
                return ScheduleUpdate(
                    interval_days=interval_days,
                    new_ease_factor=new_ef,
                    new_state=CardState.REVIEW,
                    new_learning_step=0,
                    new_lapses_count=card.lapses_count,
                    next_due=next_due
                )
            else:
                # Advance to next learning step
                # Use the interval for where we're going (next_step)
                interval_seconds = LEARNING_STEPS[next_step - 1] if next_step > 0 else LEARNING_STEPS[0]
                interval_days = interval_seconds / 86400.0
                next_due = datetime.utcnow() + timedelta(seconds=interval_seconds)
                
                return ScheduleUpdate(
                    interval_days=interval_days,
                    new_ease_factor=card.ease_factor,
                    new_state=CardState.LEARNING,
                    new_learning_step=next_step,
                    new_lapses_count=card.lapses_count,
                    next_due=next_due
                )
        else:
            # Failed: repeat current step
            interval_seconds = LEARNING_STEPS[current_step] if current_step < len(LEARNING_STEPS) else LEARNING_STEPS[0]
            interval_days = interval_seconds / 86400.0
            next_due = datetime.utcnow() + timedelta(seconds=interval_seconds)
            
            return ScheduleUpdate(
                interval_days=interval_days,
                new_ease_factor=card.ease_factor,
                new_state=CardState.LEARNING,
                new_learning_step=current_step,
                new_lapses_count=card.lapses_count,
                next_due=next_due
            )
    
    def _handle_relearning_phase(self, card: Card, quality: int) -> ScheduleUpdate:
        """
        Handle RELEARNING state cards (one-step recovery).
        
        Unlike the 3-step learning progression, RELEARNING graduates in a single
        step. Any success (q≥3) brings the card back to REVIEW state.
        
        This implements the lapse recovery mechanism: after a lapse, a single
        correct answer returns the card to review phase.
        """
        if quality >= 3:
            # One-step recovery: success → back to REVIEW
            new_ef = self.adjust_ease_factor(card.ease_factor, quality)
            interval_days = 1.0
            next_due = datetime.utcnow() + timedelta(days=interval_days)
            
            return ScheduleUpdate(
                interval_days=interval_days,
                new_ease_factor=new_ef,
                new_state=CardState.REVIEW,
                new_learning_step=0,
                new_lapses_count=card.lapses_count,
                next_due=next_due
            )
        else:
            # Failed again in relearning: stay in RELEARNING at step 0
            # Use the first learning step interval (1 minute)
            interval_seconds = LEARNING_STEPS[0]
            interval_days = interval_seconds / 86400.0
            next_due = datetime.utcnow() + timedelta(seconds=interval_seconds)
            
            return ScheduleUpdate(
                interval_days=interval_days,
                new_ease_factor=card.ease_factor,
                new_state=CardState.RELEARNING,
                new_learning_step=0,
                new_lapses_count=card.lapses_count,
                next_due=next_due
            )
    
    def _handle_review_lapse(self, card: Card) -> ScheduleUpdate:
        """Handle failed review (quality < 3) for REVIEW cards."""
        # Use handle_lapse helper
        lapse_result = self.handle_lapse(card)
        
        return ScheduleUpdate(
            interval_days=lapse_result.interval_days,
            new_ease_factor=lapse_result.new_ease_factor,
            new_state=CardState.RELEARNING,
            new_learning_step=0,
            new_lapses_count=card.lapses_count + 1,
            next_due=lapse_result.next_due
        )
    
    def _handle_review_success(self, card: Card, quality: int, 
                               difficulty_factor: float) -> ScheduleUpdate:
        """Handle successful review (quality >= 3) for REVIEW cards."""
        # Adjust ease factor
        new_ef = self.adjust_ease_factor(card.ease_factor, quality)
        
        # Calculate new interval
        current_interval = max(card.interval_days, 1.0)  # Ensure at least 1 day
        new_interval = calculate_interval(current_interval, new_ef, difficulty_factor)
        
        # Calculate next due date
        next_due = datetime.utcnow() + timedelta(days=new_interval)
        
        return ScheduleUpdate(
            interval_days=new_interval,
            new_ease_factor=new_ef,
            new_state=CardState.REVIEW,
            new_learning_step=0,
            new_lapses_count=card.lapses_count,
            next_due=next_due
        )
    
    def adjust_ease_factor(self, current_ef: float, quality: int) -> float:
        """
        Adjust ease factor based on quality rating.
        
        Formula: EF' = EF + 0.1 - (5-q)*(0.08 + (5-q)*0.02)
        Clamped to range [MIN_EF, MAX_EF]
        
        Args:
            current_ef: Current ease factor
            quality: Quality rating 0-5
        
        Returns:
            New ease factor in range [1.3, 2.5]
        
        Examples:
            >>> sm2 = SM2Plus()
            >>> sm2.adjust_ease_factor(2.5, 5)  # Perfect recall
            2.6  # Would be clamped to 2.5
            >>> sm2.adjust_ease_factor(2.5, 0)  # Complete failure
            1.7  # Significant decrease
        """
        delta = ease_factor_delta(quality)
        new_ef = current_ef + delta
        return clamp(new_ef, MIN_EF, MAX_EF)
    
    def handle_lapse(self, card: Card) -> ScheduleUpdate:
        """
        Handle a lapsed review (failed after graduation).
        
        Applies penalties:
        - EF reduced by 0.2 (floored at MIN_EF)
        - Interval halved (floored at 1 day)
        - Card enters RELEARNING state
        
        Args:
            card: Card that was failed
        
        Returns:
            ScheduleUpdate with lapse penalties applied
        
        Examples:
            >>> card = Card(..., ease_factor=2.5, interval_days=10.0)
            >>> result = sm2.handle_lapse(card)
            >>> result.new_ease_factor
            2.3
            >>> result.interval_days
            5.0
        """
        # Reduce ease factor by 0.2
        new_ef = max(card.ease_factor - 0.2, MIN_EF)
        
        # Halve interval (floor at 1 day)
        new_interval = max(card.interval_days / 2.0, 1.0)
        
        # Calculate next due (use new interval for relearning start)
        next_due = datetime.utcnow() + timedelta(days=new_interval)
        
        return ScheduleUpdate(
            interval_days=new_interval,
            new_ease_factor=new_ef,
            new_state=CardState.RELEARNING,
            new_learning_step=0,
            new_lapses_count=card.lapses_count + 1,
            next_due=next_due
        )
    
    def calculate_initial_interval(self, quality: int) -> timedelta:
        """
        Calculate interval for first review of a new card.
        
        Args:
            quality: Quality rating 0-5
        
        Returns:
            timedelta for first review interval
        
        Notes:
            - q >= 3: Advance to step 1 (1 minute)
            - q < 3: Repeat step 0 (1 minute)
        """
        # First learning step is 1 minute regardless of quality
        interval_seconds = LEARNING_STEPS[0]
        return timedelta(seconds=interval_seconds)
    
    def calculate_difficulty_factor(self, retention_rate: float) -> float:
        """
        Calculate user-specific difficulty factor.
        
        Adjusts intervals based on user's retention rate:
        - retention > 90%: Make reviews more challenging (DF > 1.0)
        - retention < 90%: Make reviews easier (DF < 1.0)
        - retention = 90%: Target rate (DF = 1.0)
        
        Formula: DF = 1.0 + (retention_rate - 0.9) × 0.5
        Clamped to [0.7, 1.3]
        
        Args:
            retention_rate: User's retention rate [0, 1]
        
        Returns:
            Difficulty factor in range [0.7, 1.3]
        
        Examples:
            >>> sm2 = SM2Plus()
            >>> sm2.calculate_difficulty_factor(0.90)  # Target rate
            1.0
            >>> sm2.calculate_difficulty_factor(0.95)  # Too easy
            1.025
            >>> sm2.calculate_difficulty_factor(0.80)  # Too hard
            0.95
        """
        df = 1.0 + (retention_rate - 0.9) * 0.5
        return clamp(df, 0.7, 1.3)
    