"""
Unit tests for sp_quiz.core.review module.

Tests cover:
- Review creation and initialization
- Field validation and constraints
- Quality rating validation (0-5 scale)
- Time validation
- State tracking
- Type hints compliance
- Edge cases and boundary conditions
- Documentation compliance (PEP 257)
"""

import unittest
from datetime import datetime, timedelta
from typing import get_type_hints
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.core.review import Review
from sp_quiz.core.card import CardState


class TestReviewCreation(unittest.TestCase):
    """Test Review creation and initialization."""
    
    def test_minimal_review_creation(self):
        """Test creating review with required fields."""
        now = datetime.datetime.utcnow()
        due_after = now + timedelta(days=1)
        
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.5,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=due_after
        )
        
        self.assertEqual(review.review_id, "rev_001")
        self.assertEqual(review.card_id, "card_001")
        self.assertEqual(review.user_id, "user_123")
        self.assertEqual(review.session_id, "session_001")
        self.assertEqual(review.quality, 4)
        self.assertEqual(review.time_taken_seconds, 5.5)
        self.assertEqual(review.state_before, CardState.NEW)
        self.assertEqual(review.interval_before, 0.0)
        self.assertEqual(review.ease_factor_before, 2.5)
        self.assertEqual(review.state_after, CardState.LEARNING)
        self.assertEqual(review.interval_after, 1.0)
        self.assertEqual(review.ease_factor_after, 2.5)
        self.assertEqual(review.due_datetime_after, due_after)
    
    def test_review_with_all_fields(self):
        """Test creating review with all fields including optional."""
        now = datetime.datetime.utcnow()
        due_after = now + timedelta(days=1)
        
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=5,
            time_taken_seconds=10.0,
            state_before=CardState.REVIEW,
            interval_before=7.0,
            ease_factor_before=2.3,
            state_after=CardState.REVIEW,
            interval_after=14.0,
            ease_factor_after=2.4,
            due_datetime_after=due_after,
            reviewed_at=now
        )
        
        self.assertEqual(review.quality, 5)
        self.assertEqual(review.reviewed_at, now)
    
    def test_reviewed_at_defaults_to_now(self):
        """Test reviewed_at defaults to current time."""
        before = datetime.datetime.utcnow()
        
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=3,
            time_taken_seconds=5.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        after = datetime.datetime.utcnow()
        
        self.assertGreaterEqual(review.reviewed_at, before)
        self.assertLessEqual(review.reviewed_at, after)


class TestReviewValidation(unittest.TestCase):
    """Test Review validation in __post_init__."""
    
    def test_quality_too_low_raises_error(self):
        """Test quality < 0 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Review(
                review_id="rev_001",
                card_id="card_001",
                user_id="user_123",
                session_id="session_001",
                quality=-1,
                time_taken_seconds=5.0,
                state_before=CardState.NEW,
                interval_before=0.0,
                ease_factor_before=2.5,
                state_after=CardState.LEARNING,
                interval_after=1.0,
                ease_factor_after=2.5,
                due_datetime_after=datetime.datetime.utcnow()
            )
        
        self.assertIn("quality must be between 0 and 5", str(context.exception))
    
    def test_quality_too_high_raises_error(self):
        """Test quality > 5 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Review(
                review_id="rev_001",
                card_id="card_001",
                user_id="user_123",
                session_id="session_001",
                quality=6,
                time_taken_seconds=5.0,
                state_before=CardState.NEW,
                interval_before=0.0,
                ease_factor_before=2.5,
                state_after=CardState.LEARNING,
                interval_after=1.0,
                ease_factor_after=2.5,
                due_datetime_after=datetime.datetime.utcnow()
            )
        
        self.assertIn("quality must be between 0 and 5", str(context.exception))
    
    def test_quality_zero_is_valid(self):
        """Test quality = 0 is valid."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=0,
            time_taken_seconds=5.0,
            state_before=CardState.REVIEW,
            interval_before=7.0,
            ease_factor_before=2.5,
            state_after=CardState.RELEARNING,
            interval_after=1.0,
            ease_factor_after=2.3,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.quality, 0)
    
    def test_quality_five_is_valid(self):
        """Test quality = 5 is valid."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=5,
            time_taken_seconds=5.0,
            state_before=CardState.REVIEW,
            interval_before=7.0,
            ease_factor_before=2.5,
            state_after=CardState.REVIEW,
            interval_after=14.0,
            ease_factor_after=2.6,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.quality, 5)
    
    def test_all_quality_levels_valid(self):
        """Test all quality levels 0-5 are valid."""
        for quality_level in range(6):
            review = Review(
                review_id=f"rev_{quality_level}",
                card_id="card_001",
                user_id="user_123",
                session_id="session_001",
                quality=quality_level,
                time_taken_seconds=5.0,
                state_before=CardState.LEARNING,
                interval_before=1.0,
                ease_factor_before=2.5,
                state_after=CardState.LEARNING,
                interval_after=1.0,
                ease_factor_after=2.5,
                due_datetime_after=datetime.datetime.utcnow()
            )
            
            self.assertEqual(review.quality, quality_level)
    
    def test_negative_time_raises_error(self):
        """Test negative time_taken_seconds raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Review(
                review_id="rev_001",
                card_id="card_001",
                user_id="user_123",
                session_id="session_001",
                quality=3,
                time_taken_seconds=-1.0,
                state_before=CardState.NEW,
                interval_before=0.0,
                ease_factor_before=2.5,
                state_after=CardState.LEARNING,
                interval_after=1.0,
                ease_factor_after=2.5,
                due_datetime_after=datetime.datetime.utcnow()
            )
        
        self.assertIn("time_taken_seconds must be non-negative", str(context.exception))
    
    def test_zero_time_is_valid(self):
        """Test time_taken_seconds = 0 is valid."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=3,
            time_taken_seconds=0.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.time_taken_seconds, 0.0)


class TestReviewTypeHints(unittest.TestCase):
    """Test that Review has proper type hints."""
    
    def test_review_has_type_hints(self):
        """Test Review class has type hints for all fields."""
        hints = get_type_hints(Review)
        
        # Check all fields have type hints
        required_fields = [
            'review_id', 'card_id', 'user_id', 'session_id',
            'quality', 'time_taken_seconds',
            'state_before', 'interval_before', 'ease_factor_before',
            'state_after', 'interval_after', 'ease_factor_after',
            'due_datetime_after', 'reviewed_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, hints, f"Missing type hint for {field}")
    
    def test_quality_type_hint(self):
        """Test quality has int type hint."""
        hints = get_type_hints(Review)
        self.assertEqual(hints['quality'], int)
    
    def test_time_type_hint(self):
        """Test time_taken_seconds has float type hint."""
        hints = get_type_hints(Review)
        self.assertEqual(hints['time_taken_seconds'], float)
    
    def test_state_type_hints(self):
        """Test state fields have CardState type hints."""
        hints = get_type_hints(Review)
        self.assertEqual(hints['state_before'], CardState)
        self.assertEqual(hints['state_after'], CardState)
    
    def test_datetime_type_hints(self):
        """Test datetime fields have datetime type hints."""
        hints = get_type_hints(Review)
        self.assertEqual(hints['due_datetime_after'], datetime)
        self.assertEqual(hints['reviewed_at'], datetime)


class TestReviewEdgeCases(unittest.TestCase):
    """Test Review edge cases and boundary conditions."""
    
    def test_very_long_review_time(self):
        """Test review with very long time taken."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=3,
            time_taken_seconds=3600.0,  # 1 hour
            state_before=CardState.REVIEW,
            interval_before=7.0,
            ease_factor_before=2.5,
            state_after=CardState.REVIEW,
            interval_after=14.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.time_taken_seconds, 3600.0)
    
    def test_fractional_seconds(self):
        """Test review with fractional seconds."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=3,
            time_taken_seconds=1.234567,
            state_before=CardState.LEARNING,
            interval_before=1.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=10.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertAlmostEqual(review.time_taken_seconds, 1.234567)
    
    def test_zero_interval_before(self):
        """Test review with zero interval before (new card)."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.interval_before, 0.0)
    
    def test_fractional_intervals(self):
        """Test review with fractional day intervals."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.0,
            state_before=CardState.LEARNING,
            interval_before=0.00069444,  # 1 minute in days
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=0.00694444,  # 10 minutes in days
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertAlmostEqual(review.interval_before, 0.00069444, places=8)
        self.assertAlmostEqual(review.interval_after, 0.00694444, places=8)
    
    def test_large_intervals(self):
        """Test review with very large intervals."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=5,
            time_taken_seconds=5.0,
            state_before=CardState.REVIEW,
            interval_before=180.0,
            ease_factor_before=2.5,
            state_after=CardState.REVIEW,
            interval_after=365.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.interval_before, 180.0)
        self.assertEqual(review.interval_after, 365.0)
    
    def test_ease_factor_changes(self):
        """Test review with ease factor changes."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=2,
            time_taken_seconds=5.0,
            state_before=CardState.REVIEW,
            interval_before=7.0,
            ease_factor_before=2.5,
            state_after=CardState.RELEARNING,
            interval_after=1.0,
            ease_factor_after=2.3,  # Decreased
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.ease_factor_before, 2.5)
        self.assertEqual(review.ease_factor_after, 2.3)
    
    def test_state_change_new_to_learning(self):
        """Test review with state change from NEW to LEARNING."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=3,
            time_taken_seconds=5.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.state_before, CardState.NEW)
        self.assertEqual(review.state_after, CardState.LEARNING)
    
    def test_state_change_learning_to_review(self):
        """Test review with state change from LEARNING to REVIEW (graduation)."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.0,
            state_before=CardState.LEARNING,
            interval_before=1.0,
            ease_factor_before=2.5,
            state_after=CardState.REVIEW,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.state_before, CardState.LEARNING)
        self.assertEqual(review.state_after, CardState.REVIEW)
    
    def test_state_change_review_to_relearning(self):
        """Test review with state change from REVIEW to RELEARNING (lapse)."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=1,
            time_taken_seconds=5.0,
            state_before=CardState.REVIEW,
            interval_before=30.0,
            ease_factor_before=2.5,
            state_after=CardState.RELEARNING,
            interval_after=1.0,
            ease_factor_after=2.3,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.state_before, CardState.REVIEW)
        self.assertEqual(review.state_after, CardState.RELEARNING)
    
    def test_no_state_change(self):
        """Test review where state doesn't change."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=3,
            time_taken_seconds=5.0,
            state_before=CardState.LEARNING,
            interval_before=1.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=10.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow()
        )
        
        self.assertEqual(review.state_before, review.state_after)


class TestReviewEquality(unittest.TestCase):
    """Test Review equality."""
    
    def test_reviews_with_same_data_are_equal(self):
        """Test reviews with identical data are equal."""
        now = datetime.datetime.utcnow()
        due = now + timedelta(days=1)
        
        review1 = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=due,
            reviewed_at=now
        )
        
        review2 = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=due,
            reviewed_at=now
        )
        
        self.assertEqual(review1, review2)
    
    def test_reviews_with_different_ids_are_not_equal(self):
        """Test reviews with different IDs are not equal."""
        now = datetime.datetime.utcnow()
        due = now + timedelta(days=1)
        
        review1 = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=due
        )
        
        review2 = Review(
            review_id="rev_002",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=due
        )
        
        self.assertNotEqual(review1, review2)


class TestReviewDocumentation(unittest.TestCase):
    """Test Review class documentation."""
    
    def test_review_class_has_docstring(self):
        """Test Review class has docstring."""
        self.assertIsNotNone(Review.__doc__)
        self.assertTrue(len(Review.__doc__) > 0)
    
    def test_review_docstring_describes_purpose(self):
        """Test Review docstring describes its purpose."""
        docstring = Review.__doc__.lower()
        self.assertTrue(
            "review" in docstring or "event" in docstring,
            "Docstring should describe the review's purpose"
        )
    
    def test_post_init_has_docstring(self):
        """Test __post_init__ has docstring."""
        self.assertIsNotNone(Review.__post_init__.__doc__)


class TestReviewStringRepresentation(unittest.TestCase):
    """Test Review string representation."""
    
    def test_review_repr(self):
        """Test Review __repr__ contains key information."""
        review = Review(
            review_id="rev_001",
            card_id="card_001",
            user_id="user_123",
            session_id="session_001",
            quality=4,
            time_taken_seconds=5.0,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.utcnow()
        )
        
        repr_str = repr(review)
        self.assertIn("rev_001", repr_str)
        self.assertIn("card_001", repr_str)


if __name__ == '__main__':
    unittest.main(verbosity=2)
