"""
Integration tests for sp_quiz Phase 1.

Tests cover:
- Integration between Card, Review, and UserProgress models
- Storage operations with real data models
- Data flow through the system
- Complex scenarios involving multiple components
"""

import unittest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.core.card import Card, CardState
from sp_quiz.core.review import Review
from sp_quiz.storage.memory import InMemoryStorage
from sp_quiz.core.exceptions import CardNotFoundError


class TestCardStorageIntegration(unittest.TestCase):
    """Test integration between Card model and Storage."""
    
    def setUp(self):
        """Set up test storage and data."""
        self.storage = InMemoryStorage()
    
    def test_full_card_lifecycle(self):
        """Test complete card lifecycle: create, read, update, delete."""
        # Create
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="What is Python?",
            back="A programming language"
        )
        
        saved_card = self.storage.save_card(card)
        self.assertIsNotNone(saved_card)
        
        # Read
        retrieved_card = self.storage.get_card("card_001")
        self.assertEqual(retrieved_card.front, "What is Python?")
        self.assertEqual(retrieved_card.state, CardState.NEW)
        
        # Update
        retrieved_card.state = CardState.LEARNING
        retrieved_card.interval_days = 1.0
        updated_card = self.storage.update_card(retrieved_card)
        self.assertEqual(updated_card.state, CardState.LEARNING)
        
        # Verify update persisted
        card_after_update = self.storage.get_card("card_001")
        self.assertEqual(card_after_update.state, CardState.LEARNING)
        self.assertEqual(card_after_update.interval_days, 1.0)
        
        # Delete
        deleted = self.storage.delete_card("card_001")
        self.assertTrue(deleted)
        
        # Verify deletion
        with self.assertRaises(CardNotFoundError):
            self.storage.get_card("card_001")
    
    def test_multiple_users_isolation(self):
        """Test that cards for different users are properly isolated."""
        # Create cards for user 1
        for i in range(3):
            card = Card(
                card_id=f"user1_card_{i}",
                user_id="user_1",
                front=f"Q{i}",
                back=f"A{i}"
            )
            self.storage.save_card(card)
        
        # Create cards for user 2
        for i in range(2):
            card = Card(
                card_id=f"user2_card_{i}",
                user_id="user_2",
                front=f"Q{i}",
                back=f"A{i}"
            )
            self.storage.save_card(card)
        
        # Verify user 1 sees only their cards
        user1_cards = self.storage.get_user_cards("user_1")
        self.assertEqual(len(user1_cards), 3)
        for card in user1_cards:
            self.assertEqual(card.user_id, "user_1")
        
        # Verify user 2 sees only their cards
        user2_cards = self.storage.get_user_cards("user_2")
        self.assertEqual(len(user2_cards), 2)
        for card in user2_cards:
            self.assertEqual(card.user_id, "user_2")


class TestReviewStorageIntegration(unittest.TestCase):
    """Test integration between Review model and Storage."""
    
    def setUp(self):
        """Set up test storage and data."""
        self.storage = InMemoryStorage()
        
        # Create a card to review
        self.card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        self.storage.save_card(self.card)
    
    def test_review_history_tracking(self):
        """Test tracking multiple reviews for a card."""
        # Simulate multiple review sessions
        reviews_data = [
            (CardState.NEW, 0.0, CardState.LEARNING, 1.0, 3),
            (CardState.LEARNING, 1.0, CardState.LEARNING, 10.0, 4),
            (CardState.LEARNING, 10.0, CardState.REVIEW, 1.0, 4),
            (CardState.REVIEW, 1.0, CardState.REVIEW, 2.5, 5),
        ]
        
        for i, (state_before, interval_before, state_after, interval_after, quality) in enumerate(reviews_data):
            review = Review(
                review_id=f"rev_{i:03d}",
                card_id="card_001",
                user_id="user_123",
                session_id="session_001",
                quality=quality,
                time_taken_seconds=5.0 + i,
                state_before=state_before,
                interval_before=interval_before,
                ease_factor_before=2.5,
                state_after=state_after,
                interval_after=interval_after,
                ease_factor_after=2.5,
                due_datetime_after=datetime.datetime.utcnow() + timedelta(days=interval_after)
            )
            self.storage.save_review(review)
        
        # Get all reviews for the card
        reviews = self.storage.get_reviews(card_id="card_001")
        
        self.assertEqual(len(reviews), 4)
        
        # Verify progression from NEW to REVIEW
        self.assertEqual(reviews[0].state_before, CardState.NEW)
        self.assertEqual(reviews[-1].state_after, CardState.REVIEW)
    
    def test_review_filtering_by_user(self):
        """Test filtering reviews by user."""
        # Create reviews for different users
        for user_num in [1, 2]:
            for i in range(3):
                review = Review(
                    review_id=f"user{user_num}_rev_{i}",
                    card_id=f"card_{i}",
                    user_id=f"user_{user_num}",
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
                self.storage.save_review(review)
        
        # Get reviews for user 1
        user1_reviews = self.storage.get_reviews(user_id="user_1")
        self.assertEqual(len(user1_reviews), 3)
        
        # Get reviews for user 2
        user2_reviews = self.storage.get_reviews(user_id="user_2")
        self.assertEqual(len(user2_reviews), 3)


class TestUserProgressIntegration(unittest.TestCase):
    """Test integration between UserProgress and other components."""
    
    def setUp(self):
        """Set up test storage and data."""
        self.storage = InMemoryStorage()
    
    def test_progress_updates_with_reviews(self):
        """Test that user progress can be updated based on reviews."""
        user_id = "user_123"
        
        # Get initial progress
        progress = self.storage.get_user_progress(user_id)
        initial_reviews = progress.total_reviews
        
        # Simulate some reviews
        for i in range(5):
            card = Card(
                card_id=f"card_{i:03d}",
                user_id=user_id,
                front=f"Q{i}",
                back=f"A{i}"
            )
            self.storage.save_card(card)
            
            review = Review(
                review_id=f"rev_{i:03d}",
                card_id=card.card_id,
                user_id=user_id,
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
            self.storage.save_review(review)
        
        # Update progress
        progress = self.storage.get_user_progress(user_id)
        progress.total_reviews = initial_reviews + 5
        progress.successful_reviews += 5  # All reviews were successful (quality 4)
        progress.reviews_today += 5
        
        updated_progress = self.storage.update_user_progress(progress)
        
        self.assertEqual(updated_progress.total_reviews, initial_reviews + 5)
        self.assertEqual(updated_progress.successful_reviews, 5)
    
    def test_card_distribution_tracking(self):
        """Test tracking card distribution across states."""
        user_id = "user_123"
        
        # Create cards in different states
        states_distribution = {
            CardState.NEW: 10,
            CardState.LEARNING: 5,
            CardState.REVIEW: 15,
            CardState.SUSPENDED: 2
        }
        
        card_counter = 0
        for state, count in states_distribution.items():
            for _ in range(count):
                card = Card(
                    card_id=f"card_{card_counter:03d}",
                    user_id=user_id,
                    front=f"Q{card_counter}",
                    back=f"A{card_counter}",
                    state=state
                )
                self.storage.save_card(card)
                card_counter += 1
        
        # Update progress to reflect card counts
        progress = self.storage.get_user_progress(user_id)
        progress.new_cards_count = states_distribution[CardState.NEW]
        progress.learning_cards_count = states_distribution[CardState.LEARNING]
        progress.review_cards_count = states_distribution[CardState.REVIEW]
        
        updated_progress = self.storage.update_user_progress(progress)
        
        self.assertEqual(updated_progress.new_cards_count, 10)
        self.assertEqual(updated_progress.learning_cards_count, 5)
        self.assertEqual(updated_progress.review_cards_count, 15)
        
        # Verify total
        total_active = (updated_progress.new_cards_count + 
                       updated_progress.learning_cards_count + 
                       updated_progress.review_cards_count)
        self.assertEqual(total_active, 30)


class TestCompleteWorkflow(unittest.TestCase):
    """Test complete workflows involving multiple components."""
    
    def setUp(self):
        """Set up test storage and data."""
        self.storage = InMemoryStorage()
    
    def test_new_user_first_session(self):
        """Test complete workflow for new user's first session."""
        user_id = "new_user_123"
        
        # 1. Get initial user progress (should be created)
        progress = self.storage.get_user_progress(user_id)
        self.assertEqual(progress.total_reviews, 0)
        self.assertEqual(progress.current_streak_days, 0)
        
        # 2. Add new cards
        cards_to_add = 5
        for i in range(cards_to_add):
            card = Card(
                card_id=f"card_{i:03d}",
                user_id=user_id,
                front=f"What is {i}?",
                back=f"Answer {i}",
                tags=["beginner", f"topic_{i % 2}"]
            )
            self.storage.save_card(card)
        
        # 3. Verify cards were added
        user_cards = self.storage.get_user_cards(user_id)
        self.assertEqual(len(user_cards), cards_to_add)
        
        # 4. Review first card
        first_card = user_cards[0]
        review = Review(
            review_id="first_review",
            card_id=first_card.card_id,
            user_id=user_id,
            session_id="first_session",
            quality=4,
            time_taken_seconds=10.5,
            state_before=CardState.NEW,
            interval_before=0.0,
            ease_factor_before=2.5,
            state_after=CardState.LEARNING,
            interval_after=1.0,
            ease_factor_after=2.5,
            due_datetime_after=datetime.datetime.utcnow() + timedelta(minutes=1)
        )
        self.storage.save_review(review)
        
        # 5. Update card state
        first_card.state = CardState.LEARNING
        first_card.interval_days = 1.0
        first_card.reviews_count = 1
        first_card.last_reviewed_at = datetime.datetime.utcnow()
        self.storage.update_card(first_card)
        
        # 6. Update user progress
        progress.total_reviews = 1
        progress.reviews_today = 1
        progress.successful_reviews = 1
        progress.new_cards_count = cards_to_add - 1
        progress.learning_cards_count = 1
        progress.current_streak_days = 1
        progress.last_review_date = datetime.datetime.utcnow()
        self.storage.update_user_progress(progress)
        
        # 7. Verify final state
        final_progress = self.storage.get_user_progress(user_id)
        self.assertEqual(final_progress.total_reviews, 1)
        self.assertEqual(final_progress.learning_cards_count, 1)
        
        final_card = self.storage.get_card(first_card.card_id)
        self.assertEqual(final_card.state, CardState.LEARNING)
        self.assertEqual(final_card.reviews_count, 1)
        
        card_reviews = self.storage.get_reviews(card_id=first_card.card_id)
        self.assertEqual(len(card_reviews), 1)
    
    def test_card_graduation_workflow(self):
        """Test complete workflow of graduating a card from learning to review."""
        user_id = "user_123"
        card_id = "grad_card_001"
        
        # Create new card
        card = Card(
            card_id=card_id,
            user_id=user_id,
            front="Graduation Test",
            back="Answer",
            state=CardState.NEW
        )
        self.storage.save_card(card)
        
        # Simulate learning phase reviews
        learning_steps = [
            (CardState.NEW, 0.0, CardState.LEARNING, 0.00069444, 4),  # 1 min
            (CardState.LEARNING, 0.00069444, CardState.LEARNING, 0.00694444, 4),  # 10 min
            (CardState.LEARNING, 0.00694444, CardState.REVIEW, 1.0, 4),  # Graduate to 1 day
        ]
        
        for i, (state_before, interval_before, state_after, interval_after, quality) in enumerate(learning_steps):
            review = Review(
                review_id=f"grad_rev_{i:03d}",
                card_id=card_id,
                user_id=user_id,
                session_id="grad_session",
                quality=quality,
                time_taken_seconds=5.0,
                state_before=state_before,
                interval_before=interval_before,
                ease_factor_before=2.5,
                state_after=state_after,
                interval_after=interval_after,
                ease_factor_after=2.5,
                due_datetime_after=datetime.datetime.utcnow() + timedelta(days=interval_after)
            )
            self.storage.save_review(review)
            
            # Update card
            card = self.storage.get_card(card_id)
            card.state = state_after
            card.interval_days = interval_after
            card.reviews_count += 1
            card.last_reviewed_at = datetime.datetime.utcnow()
            self.storage.update_card(card)
        
        # Verify final state
        final_card = self.storage.get_card(card_id)
        self.assertEqual(final_card.state, CardState.REVIEW)
        self.assertEqual(final_card.interval_days, 1.0)
        self.assertEqual(final_card.reviews_count, 3)
        
        # Verify review history
        reviews = self.storage.get_reviews(card_id=card_id)
        self.assertEqual(len(reviews), 3)
        self.assertEqual(reviews[-1].state_after, CardState.REVIEW)


class TestDataConsistency(unittest.TestCase):
    """Test data consistency across operations."""
    
    def setUp(self):
        """Set up test storage."""
        self.storage = InMemoryStorage()
    
    def test_card_review_consistency(self):
        """Test that card state and review history remain consistent."""
        user_id = "user_123"
        card_id = "card_001"
        
        # Create card
        card = Card(
            card_id=card_id,
            user_id=user_id,
            front="Question",
            back="Answer",
            state=CardState.NEW,
            reviews_count=0
        )
        self.storage.save_card(card)
        
        # Add 3 reviews
        for i in range(3):
            review = Review(
                review_id=f"rev_{i:03d}",
                card_id=card_id,
                user_id=user_id,
                session_id="session_001",
                quality=4,
                time_taken_seconds=5.0,
                state_before=CardState.LEARNING,
                interval_before=1.0,
                ease_factor_before=2.5,
                state_after=CardState.LEARNING,
                interval_after=10.0,
                ease_factor_after=2.5,
                due_datetime_after=datetime.datetime.utcnow()
            )
            self.storage.save_review(review)
        
        # Update card review count
        card = self.storage.get_card(card_id)
        card.reviews_count = 3
        self.storage.update_card(card)
        
        # Verify consistency
        final_card = self.storage.get_card(card_id)
        reviews = self.storage.get_reviews(card_id=card_id)
        
        self.assertEqual(final_card.reviews_count, len(reviews))


if __name__ == '__main__':
    unittest.main(verbosity=2)
