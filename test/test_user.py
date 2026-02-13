"""
Unit tests for sp_quiz.core.user module.

Tests cover:
- UserProgress creation and initialization
- Statistics tracking and calculations
- Streak management
- Field validation
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

from sp_quiz.core.user import UserProgress


class TestUserProgressCreation(unittest.TestCase):
    """Test UserProgress creation and initialization."""
    
    def test_minimal_user_progress_creation(self):
        """Test creating UserProgress with only required field."""
        progress = UserProgress(user_id="user_123")
        
        self.assertEqual(progress.user_id, "user_123")
    
    def test_full_user_progress_creation(self):
        """Test creating UserProgress with all fields."""
        now = datetime.datetime.utcnow()
        last_review = now - timedelta(days=1)
        
        progress = UserProgress(
            user_id="user_123",
            new_cards_count=50,
            learning_cards_count=20,
            review_cards_count=100,
            total_reviews=500,
            reviews_today=10,
            successful_reviews=450,
            current_streak_days=15,
            longest_streak_days=30,
            last_review_date=last_review,
            cards_added_last_7_days=10,
            cards_added_last_30_days=40,
            average_reviews_per_day=12.5,
            retention_rate=0.90,
            difficulty_factor=1.05,
            created_at=now,
            updated_at=now
        )
        
        self.assertEqual(progress.user_id, "user_123")
        self.assertEqual(progress.new_cards_count, 50)
        self.assertEqual(progress.learning_cards_count, 20)
        self.assertEqual(progress.review_cards_count, 100)
        self.assertEqual(progress.total_reviews, 500)
        self.assertEqual(progress.reviews_today, 10)
        self.assertEqual(progress.successful_reviews, 450)
        self.assertEqual(progress.current_streak_days, 15)
        self.assertEqual(progress.longest_streak_days, 30)
        self.assertEqual(progress.last_review_date, last_review)
        self.assertEqual(progress.cards_added_last_7_days, 10)
        self.assertEqual(progress.cards_added_last_30_days, 40)
        self.assertAlmostEqual(progress.average_reviews_per_day, 12.5)
        self.assertAlmostEqual(progress.retention_rate, 0.90)
        self.assertAlmostEqual(progress.difficulty_factor, 1.05)
        self.assertEqual(progress.created_at, now)
        self.assertEqual(progress.updated_at, now)
    
    def test_default_values(self):
        """Test default field values are set correctly."""
        progress = UserProgress(user_id="user_123")
        
        self.assertEqual(progress.new_cards_count, 0)
        self.assertEqual(progress.learning_cards_count, 0)
        self.assertEqual(progress.review_cards_count, 0)
        self.assertEqual(progress.total_reviews, 0)
        self.assertEqual(progress.reviews_today, 0)
        self.assertEqual(progress.successful_reviews, 0)
        self.assertEqual(progress.current_streak_days, 0)
        self.assertEqual(progress.longest_streak_days, 0)
        self.assertIsNone(progress.last_review_date)
        self.assertEqual(progress.cards_added_last_7_days, 0)
        self.assertEqual(progress.cards_added_last_30_days, 0)
        self.assertEqual(progress.average_reviews_per_day, 0.0)
        self.assertEqual(progress.retention_rate, 0.0)
        self.assertEqual(progress.difficulty_factor, 1.0)
        self.assertIsInstance(progress.created_at, datetime)
        self.assertIsInstance(progress.updated_at, datetime)


class TestUserProgressTypeHints(unittest.TestCase):
    """Test that UserProgress has proper type hints."""
    
    def test_user_progress_has_type_hints(self):
        """Test UserProgress class has type hints for all fields."""
        hints = get_type_hints(UserProgress)
        
        required_fields = [
            'user_id', 'new_cards_count', 'learning_cards_count',
            'review_cards_count', 'total_reviews', 'reviews_today',
            'successful_reviews', 'current_streak_days', 'longest_streak_days',
            'last_review_date', 'cards_added_last_7_days', 'cards_added_last_30_days',
            'average_reviews_per_day', 'retention_rate', 'difficulty_factor',
            'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, hints, f"Missing type hint for {field}")
    
    def test_user_id_type_hint(self):
        """Test user_id has str type hint."""
        hints = get_type_hints(UserProgress)
        self.assertEqual(hints['user_id'], str)
    
    def test_count_type_hints(self):
        """Test count fields have int type hints."""
        hints = get_type_hints(UserProgress)
        self.assertEqual(hints['new_cards_count'], int)
        self.assertEqual(hints['learning_cards_count'], int)
        self.assertEqual(hints['review_cards_count'], int)
        self.assertEqual(hints['total_reviews'], int)
        self.assertEqual(hints['reviews_today'], int)
        self.assertEqual(hints['successful_reviews'], int)
    
    def test_float_type_hints(self):
        """Test float fields have float type hints."""
        hints = get_type_hints(UserProgress)
        self.assertEqual(hints['average_reviews_per_day'], float)
        self.assertEqual(hints['retention_rate'], float)
        self.assertEqual(hints['difficulty_factor'], float)


class TestUserProgressCardCounts(unittest.TestCase):
    """Test UserProgress card count tracking."""
    
    def test_zero_card_counts(self):
        """Test all card counts start at zero."""
        progress = UserProgress(user_id="user_123")
        
        self.assertEqual(progress.new_cards_count, 0)
        self.assertEqual(progress.learning_cards_count, 0)
        self.assertEqual(progress.review_cards_count, 0)
    
    def test_positive_card_counts(self):
        """Test setting positive card counts."""
        progress = UserProgress(
            user_id="user_123",
            new_cards_count=100,
            learning_cards_count=50,
            review_cards_count=200
        )
        
        self.assertEqual(progress.new_cards_count, 100)
        self.assertEqual(progress.learning_cards_count, 50)
        self.assertEqual(progress.review_cards_count, 200)
    
    def test_large_card_counts(self):
        """Test very large card counts."""
        progress = UserProgress(
            user_id="user_123",
            new_cards_count=10000,
            learning_cards_count=5000,
            review_cards_count=50000
        )
        
        self.assertEqual(progress.new_cards_count, 10000)
        self.assertEqual(progress.learning_cards_count, 5000)
        self.assertEqual(progress.review_cards_count, 50000)
    
    def test_total_cards_calculation(self):
        """Test calculating total cards."""
        progress = UserProgress(
            user_id="user_123",
            new_cards_count=100,
            learning_cards_count=50,
            review_cards_count=200
        )
        
        total = (progress.new_cards_count + 
                progress.learning_cards_count + 
                progress.review_cards_count)
        
        self.assertEqual(total, 350)


class TestUserProgressReviewStats(unittest.TestCase):
    """Test UserProgress review statistics."""
    
    def test_zero_reviews(self):
        """Test initial state with no reviews."""
        progress = UserProgress(user_id="user_123")
        
        self.assertEqual(progress.total_reviews, 0)
        self.assertEqual(progress.reviews_today, 0)
        self.assertEqual(progress.successful_reviews, 0)
    
    def test_successful_review_tracking(self):
        """Test tracking successful reviews."""
        progress = UserProgress(
            user_id="user_123",
            total_reviews=100,
            successful_reviews=90
        )
        
        self.assertEqual(progress.total_reviews, 100)
        self.assertEqual(progress.successful_reviews, 90)
    
    def test_all_reviews_successful(self):
        """Test when all reviews are successful."""
        progress = UserProgress(
            user_id="user_123",
            total_reviews=100,
            successful_reviews=100
        )
        
        self.assertEqual(progress.successful_reviews, progress.total_reviews)
    
    def test_no_successful_reviews(self):
        """Test when no reviews are successful."""
        progress = UserProgress(
            user_id="user_123",
            total_reviews=50,
            successful_reviews=0
        )
        
        self.assertEqual(progress.successful_reviews, 0)
    
    def test_reviews_today_tracking(self):
        """Test tracking reviews done today."""
        progress = UserProgress(
            user_id="user_123",
            total_reviews=1000,
            reviews_today=25
        )
        
        self.assertEqual(progress.reviews_today, 25)
        self.assertLessEqual(progress.reviews_today, progress.total_reviews)


class TestUserProgressStreaks(unittest.TestCase):
    """Test UserProgress streak tracking."""
    
    def test_zero_streaks(self):
        """Test initial state with no streaks."""
        progress = UserProgress(user_id="user_123")
        
        self.assertEqual(progress.current_streak_days, 0)
        self.assertEqual(progress.longest_streak_days, 0)
    
    def test_current_streak(self):
        """Test tracking current streak."""
        progress = UserProgress(
            user_id="user_123",
            current_streak_days=7
        )
        
        self.assertEqual(progress.current_streak_days, 7)
    
    def test_longest_streak(self):
        """Test tracking longest streak."""
        progress = UserProgress(
            user_id="user_123",
            current_streak_days=10,
            longest_streak_days=30
        )
        
        self.assertEqual(progress.current_streak_days, 10)
        self.assertEqual(progress.longest_streak_days, 30)
    
    def test_current_equals_longest(self):
        """Test when current streak equals longest."""
        progress = UserProgress(
            user_id="user_123",
            current_streak_days=15,
            longest_streak_days=15
        )
        
        self.assertEqual(progress.current_streak_days, progress.longest_streak_days)
    
    def test_very_long_streaks(self):
        """Test very long streak values."""
        progress = UserProgress(
            user_id="user_123",
            current_streak_days=365,
            longest_streak_days=500
        )
        
        self.assertEqual(progress.current_streak_days, 365)
        self.assertEqual(progress.longest_streak_days, 500)
    
    def test_last_review_date_tracking(self):
        """Test tracking last review date."""
        yesterday = datetime.datetime.utcnow() - timedelta(days=1)
        progress = UserProgress(
            user_id="user_123",
            last_review_date=yesterday
        )
        
        self.assertEqual(progress.last_review_date, yesterday)
    
    def test_last_review_date_none_initially(self):
        """Test last_review_date is None for new user."""
        progress = UserProgress(user_id="user_123")
        
        self.assertIsNone(progress.last_review_date)


class TestUserProgressVelocityMetrics(unittest.TestCase):
    """Test UserProgress velocity and rate metrics."""
    
    def test_cards_added_tracking(self):
        """Test tracking cards added over time periods."""
        progress = UserProgress(
            user_id="user_123",
            cards_added_last_7_days=15,
            cards_added_last_30_days=50
        )
        
        self.assertEqual(progress.cards_added_last_7_days, 15)
        self.assertEqual(progress.cards_added_last_30_days, 50)
    
    def test_average_reviews_per_day(self):
        """Test average reviews per day calculation."""
        progress = UserProgress(
            user_id="user_123",
            average_reviews_per_day=25.5
        )
        
        self.assertAlmostEqual(progress.average_reviews_per_day, 25.5)
    
    def test_zero_average_reviews(self):
        """Test zero average when no reviews."""
        progress = UserProgress(user_id="user_123")
        
        self.assertEqual(progress.average_reviews_per_day, 0.0)
    
    def test_fractional_average_reviews(self):
        """Test fractional average reviews."""
        progress = UserProgress(
            user_id="user_123",
            average_reviews_per_day=12.345
        )
        
        self.assertAlmostEqual(progress.average_reviews_per_day, 12.345, places=3)
    
    def test_high_velocity(self):
        """Test high learning velocity."""
        progress = UserProgress(
            user_id="user_123",
            cards_added_last_7_days=100,
            cards_added_last_30_days=400,
            average_reviews_per_day=50.0
        )
        
        self.assertEqual(progress.cards_added_last_7_days, 100)
        self.assertEqual(progress.cards_added_last_30_days, 400)
        self.assertEqual(progress.average_reviews_per_day, 50.0)


class TestUserProgressRetention(unittest.TestCase):
    """Test UserProgress retention rate tracking."""
    
    def test_zero_retention(self):
        """Test zero retention rate."""
        progress = UserProgress(
            user_id="user_123",
            retention_rate=0.0
        )
        
        self.assertEqual(progress.retention_rate, 0.0)
    
    def test_perfect_retention(self):
        """Test 100% retention rate."""
        progress = UserProgress(
            user_id="user_123",
            retention_rate=1.0
        )
        
        self.assertEqual(progress.retention_rate, 1.0)
    
    def test_ninety_percent_retention(self):
        """Test 90% retention (target rate)."""
        progress = UserProgress(
            user_id="user_123",
            retention_rate=0.90
        )
        
        self.assertAlmostEqual(progress.retention_rate, 0.90)
    
    def test_retention_as_percentage(self):
        """Test various retention percentages."""
        test_rates = [0.0, 0.25, 0.50, 0.75, 0.85, 0.90, 0.95, 1.0]
        
        for rate in test_rates:
            progress = UserProgress(
                user_id="user_123",
                retention_rate=rate
            )
            self.assertAlmostEqual(progress.retention_rate, rate)
    
    def test_retention_from_successful_reviews(self):
        """Test calculating retention from successful reviews."""
        progress = UserProgress(
            user_id="user_123",
            total_reviews=100,
            successful_reviews=85
        )
        
        # Calculate retention manually
        if progress.total_reviews > 0:
            calculated_retention = progress.successful_reviews / progress.total_reviews
            self.assertAlmostEqual(calculated_retention, 0.85)


class TestUserProgressDifficultyFactor(unittest.TestCase):
    """Test UserProgress difficulty factor adjustments."""
    
    def test_default_difficulty_factor(self):
        """Test default difficulty factor is 1.0."""
        progress = UserProgress(user_id="user_123")
        
        self.assertEqual(progress.difficulty_factor, 1.0)
    
    def test_increased_difficulty(self):
        """Test increased difficulty factor."""
        progress = UserProgress(
            user_id="user_123",
            difficulty_factor=1.2
        )
        
        self.assertAlmostEqual(progress.difficulty_factor, 1.2)
    
    def test_decreased_difficulty(self):
        """Test decreased difficulty factor."""
        progress = UserProgress(
            user_id="user_123",
            difficulty_factor=0.8
        )
        
        self.assertAlmostEqual(progress.difficulty_factor, 0.8)
    
    def test_difficulty_factor_bounds(self):
        """Test difficulty factor within expected bounds (0.7-1.3)."""
        min_df = 0.7
        max_df = 1.3
        
        progress_min = UserProgress(
            user_id="user_123",
            difficulty_factor=min_df
        )
        progress_max = UserProgress(
            user_id="user_123",
            difficulty_factor=max_df
        )
        
        self.assertAlmostEqual(progress_min.difficulty_factor, min_df)
        self.assertAlmostEqual(progress_max.difficulty_factor, max_df)
    
    def test_difficulty_factor_precision(self):
        """Test difficulty factor with high precision."""
        progress = UserProgress(
            user_id="user_123",
            difficulty_factor=1.05432
        )
        
        self.assertAlmostEqual(progress.difficulty_factor, 1.05432, places=5)


class TestUserProgressTimestamps(unittest.TestCase):
    """Test UserProgress timestamp handling."""
    
    def test_created_at_defaults_to_now(self):
        """Test created_at defaults to current time."""
        before = datetime.datetime.utcnow()
        progress = UserProgress(user_id="user_123")
        after = datetime.datetime.utcnow()
        
        self.assertGreaterEqual(progress.created_at, before)
        self.assertLessEqual(progress.created_at, after)
    
    def test_updated_at_defaults_to_now(self):
        """Test updated_at defaults to current time."""
        before = datetime.datetime.utcnow()
        progress = UserProgress(user_id="user_123")
        after = datetime.datetime.utcnow()
        
        self.assertGreaterEqual(progress.updated_at, before)
        self.assertLessEqual(progress.updated_at, after)
    
    def test_explicit_timestamps(self):
        """Test setting explicit timestamps."""
        created = datetime(2024, 1, 1, 12, 0, 0)
        updated = datetime(2024, 1, 2, 12, 0, 0)
        
        progress = UserProgress(
            user_id="user_123",
            created_at=created,
            updated_at=updated
        )
        
        self.assertEqual(progress.created_at, created)
        self.assertEqual(progress.updated_at, updated)


class TestUserProgressEdgeCases(unittest.TestCase):
    """Test UserProgress edge cases and boundary conditions."""
    
    def test_negative_card_counts(self):
        """Test negative card counts (edge case)."""
        progress = UserProgress(
            user_id="user_123",
            new_cards_count=-1,
            learning_cards_count=-1,
            review_cards_count=-1
        )
        
        self.assertEqual(progress.new_cards_count, -1)
        self.assertEqual(progress.learning_cards_count, -1)
        self.assertEqual(progress.review_cards_count, -1)
    
    def test_negative_reviews(self):
        """Test negative review counts (edge case)."""
        progress = UserProgress(
            user_id="user_123",
            total_reviews=-10,
            successful_reviews=-5
        )
        
        self.assertEqual(progress.total_reviews, -10)
        self.assertEqual(progress.successful_reviews, -5)
    
    def test_more_successful_than_total(self):
        """Test successful reviews > total reviews (inconsistent state)."""
        progress = UserProgress(
            user_id="user_123",
            total_reviews=50,
            successful_reviews=60
        )
        
        self.assertGreater(progress.successful_reviews, progress.total_reviews)
    
    def test_negative_streaks(self):
        """Test negative streak values (edge case)."""
        progress = UserProgress(
            user_id="user_123",
            current_streak_days=-5,
            longest_streak_days=-10
        )
        
        self.assertEqual(progress.current_streak_days, -5)
        self.assertEqual(progress.longest_streak_days, -10)
    
    def test_current_streak_longer_than_longest(self):
        """Test current streak > longest streak (inconsistent state)."""
        progress = UserProgress(
            user_id="user_123",
            current_streak_days=20,
            longest_streak_days=10
        )
        
        self.assertGreater(progress.current_streak_days, progress.longest_streak_days)
    
    def test_retention_rate_over_one(self):
        """Test retention rate > 1.0 (edge case)."""
        progress = UserProgress(
            user_id="user_123",
            retention_rate=1.5
        )
        
        self.assertEqual(progress.retention_rate, 1.5)
    
    def test_negative_retention_rate(self):
        """Test negative retention rate (edge case)."""
        progress = UserProgress(
            user_id="user_123",
            retention_rate=-0.1
        )
        
        self.assertEqual(progress.retention_rate, -0.1)
    
    def test_extreme_difficulty_factors(self):
        """Test extreme difficulty factor values."""
        progress_low = UserProgress(
            user_id="user_123",
            difficulty_factor=0.1
        )
        progress_high = UserProgress(
            user_id="user_123",
            difficulty_factor=10.0
        )
        
        self.assertAlmostEqual(progress_low.difficulty_factor, 0.1)
        self.assertAlmostEqual(progress_high.difficulty_factor, 10.0)
    
    def test_unicode_user_id(self):
        """Test UserProgress with Unicode user ID."""
        progress = UserProgress(user_id="用户_123")
        
        self.assertEqual(progress.user_id, "用户_123")
    
    def test_very_long_user_id(self):
        """Test UserProgress with very long user ID."""
        long_id = "user_" + "x" * 1000
        progress = UserProgress(user_id=long_id)
        
        self.assertEqual(progress.user_id, long_id)
        self.assertEqual(len(progress.user_id), 1005)


class TestUserProgressEquality(unittest.TestCase):
    """Test UserProgress equality."""
    
    def test_user_progress_with_same_data_are_equal(self):
        """Test UserProgress with identical data are equal."""
        now = datetime.datetime.utcnow()
        
        progress1 = UserProgress(
            user_id="user_123",
            new_cards_count=50,
            created_at=now,
            updated_at=now
        )
        
        progress2 = UserProgress(
            user_id="user_123",
            new_cards_count=50,
            created_at=now,
            updated_at=now
        )
        
        self.assertEqual(progress1, progress2)
    
    def test_user_progress_with_different_ids_are_not_equal(self):
        """Test UserProgress with different IDs are not equal."""
        progress1 = UserProgress(user_id="user_123")
        progress2 = UserProgress(user_id="user_456")
        
        self.assertNotEqual(progress1, progress2)


class TestUserProgressDocumentation(unittest.TestCase):
    """Test UserProgress class documentation."""
    
    def test_user_progress_class_has_docstring(self):
        """Test UserProgress class has docstring."""
        self.assertIsNotNone(UserProgress.__doc__)
        self.assertTrue(len(UserProgress.__doc__) > 0)
    
    def test_user_progress_docstring_describes_purpose(self):
        """Test UserProgress docstring describes its purpose."""
        docstring = UserProgress.__doc__.lower()
        self.assertTrue(
            "progress" in docstring or "track" in docstring or "statistics" in docstring,
            "Docstring should describe the progress tracking purpose"
        )


class TestUserProgressStringRepresentation(unittest.TestCase):
    """Test UserProgress string representation."""
    
    def test_user_progress_repr(self):
        """Test UserProgress __repr__ contains key information."""
        progress = UserProgress(user_id="user_123")
        
        repr_str = repr(progress)
        self.assertIn("user_123", repr_str)


if __name__ == '__main__':
    unittest.main(verbosity=2)
