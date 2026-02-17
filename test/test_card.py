"""
Unit tests for sp_quiz.core.card module.

Tests cover:
- Card creation and initialization
- Field validation and constraints
- State transitions
- Immutability where required
- Type hints compliance
- Edge cases and boundary conditions
- Documentation compliance (PEP 257)
"""

import unittest
from datetime import datetime, timedelta
from dataclasses import FrozenInstanceError
from typing import get_type_hints
import sys
import os

#parent dir addition to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.core.card import Card, CardState
from sp_quiz.core.exceptions import InvalidCardStateError

class TestCardState(unittest.TestCase):
    """Test CardState emum."""

    def test_card_state_values(self):
        """Test all CardState enum values are defined correctly."""
        self.assertEqual(CardState.NEW.value, "new")
        self.assertEqual(CardState.LEARNING.value, "learning")
        self.assertEqual(CardState.REVIEW.value, "review")
        self.assertEqual(CardState.RELEARNING.value, "relearning")
        self.assertEqual(CardState.SUSPENDED.value, "suspended")
    
    def test_card_state_membership(self):
        """Test CardState enum membership."""
        valid_states = {CardState.NEW, CardState.LEARNING, CardState.REVIEW, 
                       CardState.RELEARNING, CardState.SUSPENDED}
        self.assertEqual(set(CardState), valid_states)
    
    def test_card_state_iteration(self):
        """Test CardState enum can be iterated."""
        states = list(CardState)
        self.assertEqual(len(states), 5)
        self.assertIn(CardState.NEW, states)


class TestCardCreation(unittest.TestCase):
    """Test Card Creation and Initialization"""

    def test_minimal_card_creation(self):
        """Test creating card with only required fields."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        
        self.assertEqual(card.card_id, "card_001")
        self.assertEqual(card.user_id, "user_123")
        self.assertEqual(card.front, "Question")
        self.assertEqual(card.back, "Answer")
    
    def test_full_card_creation(self):
        """Test creating card with all fields."""
        now = datetime.utcnow()
        due = now + timedelta(days=1)
        
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="What is Python?",
            back="A programming language",
            tags=["programming", "python"],
            metadata={"difficulty": "easy", "source": "book"},
            state=CardState.REVIEW,
            due_datetime=due,
            interval_days=7.5,
            ease_factor=2.3,
            learning_step=0,
            reviews_count=5,
            lapses_count=1,
            average_quality=4.2,
            created_at=now,
            updated_at=now,
            last_reviewed_at=now
        )
        
        self.assertEqual(card.card_id, "card_001")
        self.assertEqual(card.user_id, "user_123")
        self.assertEqual(card.tags, ["programming", "python"])
        self.assertEqual(card.metadata["difficulty"], "easy")
        self.assertEqual(card.state, CardState.REVIEW)
        self.assertEqual(card.due_datetime, due)
        self.assertEqual(card.interval_days, 7.5)
        self.assertEqual(card.ease_factor, 2.3)
        self.assertEqual(card.reviews_count, 5)
        self.assertEqual(card.lapses_count, 1)
        self.assertAlmostEqual(card.average_quality, 4.2)
    
    def test_default_values(self):
        """Test default field values are set correctly."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A"
        )
        
        self.assertEqual(card.tags, [])
        self.assertEqual(card.metadata, {})
        self.assertEqual(card.state, CardState.NEW)
        self.assertIsNone(card.due_datetime)
        self.assertEqual(card.interval_days, 0.0)
        self.assertEqual(card.ease_factor, 2.5)
        self.assertEqual(card.learning_step, 0)
        self.assertEqual(card.reviews_count, 0)
        self.assertEqual(card.lapses_count, 0)
        self.assertEqual(card.average_quality, 0.0)
        self.assertIsInstance(card.created_at, datetime)
        self.assertIsInstance(card.updated_at, datetime)
        self.assertIsNone(card.last_reviewed_at)
    
    def test_tags_default_factory(self):
        """Test that tags default to empty list and are independent."""
        card1 = Card(card_id="1", user_id="u1", front="Q1", back="A1")
        card2 = Card(card_id="2", user_id="u2", front="Q2", back="A2")
        
        card1.tags.append("tag1")
        
        self.assertEqual(card1.tags, ["tag1"])
        self.assertEqual(card2.tags, [])
    
    def test_metadata_default_factory(self):
        """Test that metadata default to empty dict and are independent."""
        card1 = Card(card_id="1", user_id="u1", front="Q1", back="A1")
        card2 = Card(card_id="2", user_id="u2", front="Q2", back="A2")
        
        card1.metadata["key"] = "value"
        
        self.assertEqual(card1.metadata, {"key": "value"})
        self.assertEqual(card2.metadata, {})


class TestCardValidation(unittest.TestCase):
    """Test Card validation in __post_init__."""
    
    def test_missing_card_id_raises_error(self):
        """Test that missing card_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="", user_id="user_123", front="Q", back="A")
        
        self.assertIn("card_id and user_id are required", str(context.exception))
    
    def test_none_card_id_raises_error(self):
        """Test that None card_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id=None, user_id="user_123", front="Q", back="A")
        
        self.assertIn("card_id and user_id are required", str(context.exception))
    
    def test_missing_user_id_raises_error(self):
        """Test that missing user_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="card_001", user_id="", front="Q", back="A")
        
        self.assertIn("card_id and user_id are required", str(context.exception))
    
    def test_none_user_id_raises_error(self):
        """Test that None user_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="card_001", user_id=None, front="Q", back="A")
        
        self.assertIn("card_id and user_id are required", str(context.exception))
    
    def test_missing_front_raises_error(self):
        """Test that missing front content raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="card_001", user_id="user_123", front="", back="A")
        
        self.assertIn("front and back content are required", str(context.exception))
    
    def test_none_front_raises_error(self):
        """Test that None front content raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="card_001", user_id="user_123", front=None, back="A")
        
        self.assertIn("front and back content are required", str(context.exception))
    
    def test_missing_back_raises_error(self):
        """Test that missing back content raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="card_001", user_id="user_123", front="Q", back="")
        
        self.assertIn("front and back content are required", str(context.exception))
    
    def test_none_back_raises_error(self):
        """Test that None back content raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="card_001", user_id="user_123", front="Q", back=None)
        
        self.assertIn("front and back content are required", str(context.exception))
    
    def test_whitespace_only_card_id_raises_error(self):
        """Test that whitespace-only card_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="   ", user_id="user_123", front="Q", back="A")
        
        self.assertIn("card_id and user_id are required", str(context.exception))

    def test_whitespace_only_front_raises_error(self):
        """Test that whitespace-only front raises ValueError."""
        with self.assertRaises(ValueError) as context:
            Card(card_id="card_001", user_id="user_123", front="   ", back="A")
        
        self.assertIn("front and back content are required", str(context.exception))


class TestCardTypeHints(unittest.TestCase):
    """Test that Card has proper type hints."""
    
    def test_card_has_type_hints(self):
        """Test that Card class has type hints for all fields."""
        hints = get_type_hints(Card)
        
        # Check all required fields have type hints
        self.assertIn('card_id', hints)
        self.assertIn('user_id', hints)
        self.assertIn('front', hints)
        self.assertIn('back', hints)
        self.assertIn('tags', hints)
        self.assertIn('metadata', hints)
        self.assertIn('state', hints)
        self.assertIn('due_datetime', hints)
        self.assertIn('interval_days', hints)
        self.assertIn('ease_factor', hints)
        self.assertIn('learning_step', hints)
        self.assertIn('reviews_count', hints)
        self.assertIn('lapses_count', hints)
        self.assertIn('average_quality', hints)
        self.assertIn('created_at', hints)
        self.assertIn('updated_at', hints)
        self.assertIn('last_reviewed_at', hints)
    
    def test_card_id_type_hint(self):
        """Test card_id has correct type hint."""
        hints = get_type_hints(Card)
        self.assertEqual(hints['card_id'], str)
    
    def test_state_type_hint(self):
        """Test state has correct type hint."""
        hints = get_type_hints(Card)
        self.assertEqual(hints['state'], CardState)


class TestCardEquality(unittest.TestCase):
    """Test Card equality and hashing."""
    
    def test_cards_with_same_data_are_equal(self):
        """Test that cards with identical data are equal."""
        now = datetime.utcnow()
        
        card1 = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            created_at=now,
            updated_at=now
        )
        
        card2 = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            created_at=now,
            updated_at=now
        )
        
        self.assertEqual(card1, card2)
    
    def test_cards_with_different_ids_are_not_equal(self):
        """Test that cards with different IDs are not equal."""
        card1 = Card(card_id="card_001", user_id="user_123", front="Q", back="A")
        card2 = Card(card_id="card_002", user_id="user_123", front="Q", back="A")
        
        self.assertNotEqual(card1, card2)
    
    def test_cards_with_different_content_are_not_equal(self):
        """Test that cards with different content are not equal."""
        card1 = Card(card_id="card_001", user_id="user_123", front="Q1", back="A1")
        card2 = Card(card_id="card_001", user_id="user_123", front="Q2", back="A2")
        
        self.assertNotEqual(card1, card2)


class TestCardStringRepresentation(unittest.TestCase):
    """Test Card string representation."""
    
    def test_card_repr(self):
        """Test Card __repr__ contains key information."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        
        repr_str = repr(card)
        self.assertIn("card_001", repr_str)
        self.assertIn("user_123", repr_str)
    
    def test_card_str(self):
        """Test Card __str__ is informative."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        
        str_repr = str(card)
        self.assertIsInstance(str_repr, str)
        self.assertTrue(len(str_repr) > 0)


class TestCardEdgeCases(unittest.TestCase):
    """Test Card edge cases and boundary conditions."""
    
    def test_very_long_front_content(self):
        """Test card with very long front content."""
        long_text = "Q" * 10000
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front=long_text,
            back="A"
        )
        
        self.assertEqual(len(card.front), 10000)
    
    def test_very_long_back_content(self):
        """Test card with very long back content."""
        long_text = "A" * 10000
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back=long_text
        )
        
        self.assertEqual(len(card.back), 10000)
    
    def test_unicode_content(self):
        """Test card with Unicode content."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="What is 日本?",
            back="Japan (日本)"
        )
        
        self.assertEqual(card.front, "What is 日本?")
        self.assertEqual(card.back, "Japan (日本)")
    
    def test_emoji_content(self):
        """Test card with emoji content."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="What does 😀 mean?",
            back="Happy face emoji"
        )
        
        self.assertIn("😀", card.front)
    
    def test_special_characters_in_content(self):
        """Test card with special characters."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="What is <div>?",
            back="An HTML element with & and \" quotes"
        )
        
        self.assertIn("<div>", card.front)
        self.assertIn("&", card.back)
        self.assertIn('"', card.back)
    
    def test_newlines_in_content(self):
        """Test card with newlines in content."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Line 1\nLine 2\nLine 3",
            back="Answer\nwith\nmultiple\nlines"
        )
        
        self.assertEqual(card.front.count('\n'), 2)
        self.assertEqual(card.back.count('\n'), 3)
    
    def test_zero_ease_factor(self):
        """Test card with zero ease factor."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            ease_factor=0.0
        )
        
        self.assertEqual(card.ease_factor, 0.0)
    
    def test_negative_ease_factor(self):
        """Test card with negative ease factor (edge case)."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            ease_factor=-1.0
        )
        
        self.assertEqual(card.ease_factor, -1.0)
    
    def test_very_large_ease_factor(self):
        """Test card with very large ease factor."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            ease_factor=100.0
        )
        
        self.assertEqual(card.ease_factor, 100.0)
    
    def test_negative_interval(self):
        """Test card with negative interval."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            interval_days=-5.0
        )
        
        self.assertEqual(card.interval_days, -5.0)
    
    def test_zero_interval(self):
        """Test card with zero interval."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            interval_days=0.0
        )
        
        self.assertEqual(card.interval_days, 0.0)
    
    def test_fractional_interval(self):
        """Test card with fractional interval."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            interval_days=0.5
        )
        
        self.assertEqual(card.interval_days, 0.5)
    
    def test_negative_reviews_count(self):
        """Test card with negative reviews count (edge case)."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            reviews_count=-1
        )
        
        self.assertEqual(card.reviews_count, -1)
    
    def test_negative_lapses_count(self):
        """Test card with negative lapses count (edge case)."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            lapses_count=-1
        )
        
        self.assertEqual(card.lapses_count, -1)
    
    def test_many_tags(self):
        """Test card with many tags."""
        many_tags = [f"tag_{i}" for i in range(100)]
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            tags=many_tags
        )
        
        self.assertEqual(len(card.tags), 100)
    
    def test_empty_tags_list(self):
        """Test card with explicitly empty tags list."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            tags=[]
        )
        
        self.assertEqual(card.tags, [])
    
    def test_complex_metadata(self):
        """Test card with complex nested metadata."""
        metadata = {
            "source": "book",
            "chapter": 5,
            "difficulty": "hard",
            "nested": {
                "key1": "value1",
                "key2": [1, 2, 3]
            },
            "list": ["a", "b", "c"]
        }
        
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            metadata=metadata
        )
        
        self.assertEqual(card.metadata["nested"]["key1"], "value1")
        self.assertEqual(card.metadata["list"], ["a", "b", "c"])
    
    def test_future_due_date(self):
        """Test card with due date far in the future."""
        far_future = datetime.utcnow() + timedelta(days=36500)  # 100 years
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            due_datetime=far_future
        )
        
        self.assertEqual(card.due_datetime, far_future)
    
    def test_past_due_date(self):
        """Test card with due date in the past."""
        past = datetime.utcnow() - timedelta(days=365)
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            due_datetime=past
        )
        
        self.assertEqual(card.due_datetime, past)


class TestCardDocumentation(unittest.TestCase):
    """Test that Card class has proper documentation."""
    
    def test_card_class_has_docstring(self):
        """Test Card class has docstring."""
        self.assertIsNotNone(Card.__doc__)
        self.assertTrue(len(Card.__doc__) > 0)
    
    def test_card_docstring_describes_purpose(self):
        """Test Card docstring describes its purpose."""
        docstring = Card.__doc__.lower()
        self.assertTrue(
            "flashcard" in docstring or "card" in docstring,
            "Docstring should describe the card's purpose"
        )
    
    def test_post_init_has_docstring(self):
        """Test __post_init__ has docstring."""
        self.assertIsNotNone(Card.__post_init__.__doc__)


class TestCardStateTransitions(unittest.TestCase):
    """Test valid card state transitions."""
    
    def test_new_to_learning_transition(self):
        """Test transitioning from NEW to LEARNING state."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            state=CardState.NEW
        )
        
        # Simulate state change (would normally be done through manager)
        card.state = CardState.LEARNING
        self.assertEqual(card.state, CardState.LEARNING)
    
    def test_learning_to_review_transition(self):
        """Test transitioning from LEARNING to REVIEW state."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            state=CardState.LEARNING
        )
        
        card.state = CardState.REVIEW
        self.assertEqual(card.state, CardState.REVIEW)
    
    def test_review_to_relearning_transition(self):
        """Test transitioning from REVIEW to RELEARNING state."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            state=CardState.REVIEW
        )
        
        card.state = CardState.RELEARNING
        self.assertEqual(card.state, CardState.RELEARNING)
    
    def test_any_to_suspended_transition(self):
        """Test transitioning from any state to SUSPENDED."""
        for initial_state in CardState:
            card = Card(
                card_id="card_001",
                user_id="user_123",
                front="Q",
                back="A",
                state=initial_state
            )
            
            card.state = CardState.SUSPENDED
            self.assertEqual(card.state, CardState.SUSPENDED)


class TestCardTimestamps(unittest.TestCase):
    """Test Card timestamp handling."""
    
    def test_created_at_defaults_to_now(self):
        """Test created_at defaults to current time."""
        before = datetime.utcnow()
        card = Card(card_id="card_001", user_id="user_123", front="Q", back="A")
        after = datetime.utcnow()
        
        self.assertGreaterEqual(card.created_at, before)
        self.assertLessEqual(card.created_at, after)
    
    def test_updated_at_defaults_to_now(self):
        """Test updated_at defaults to current time."""
        before = datetime.utcnow()
        card = Card(card_id="card_001", user_id="user_123", front="Q", back="A")
        after = datetime.utcnow()
        
        self.assertGreaterEqual(card.updated_at, before)
        self.assertLessEqual(card.updated_at, after)
    
    def test_last_reviewed_at_defaults_to_none(self):
        """Test last_reviewed_at defaults to None."""
        card = Card(card_id="card_001", user_id="user_123", front="Q", back="A")
        self.assertIsNone(card.last_reviewed_at)
    
    def test_explicit_timestamps(self):
        """Test setting explicit timestamps."""
        created = datetime(2024, 1, 1, 12, 0, 0)
        updated = datetime(2024, 1, 2, 12, 0, 0)
        reviewed = datetime(2024, 1, 3, 12, 0, 0)
        
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q",
            back="A",
            created_at=created,
            updated_at=updated,
            last_reviewed_at=reviewed
        )
        
        self.assertEqual(card.created_at, created)
        self.assertEqual(card.updated_at, updated)
        self.assertEqual(card.last_reviewed_at, reviewed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
