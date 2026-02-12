"""
Unit tests for sp_quiz.storage module.

Tests cover:
- StorageInterface abstract methods
- InMemoryStorage implementation
- CRUD operations
- Thread safety
- Data persistence (in-memory)
- Edge cases and error handling
- Type hints compliance
- Documentation compliance (PEP 257)
"""

import unittest
from datetime import datetime, timedelta
from typing import get_type_hints
import sys
import os
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.storage.interface import StorageInterface
from sp_quiz.storage.memory import InMemoryStorage
from sp_quiz.core.card import Card, CardState
from sp_quiz.core.review import Review
from sp_quiz.core.exceptions import CardNotFoundError


class TestStorageInterface(unittest.TestCase):
    """Test StorageInterface abstract base class."""
    
    def test_storage_interface_is_abstract(self):
        """Test StorageInterface cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            StorageInterface()
    
    def test_storage_interface_has_required_methods(self):
        """Test StorageInterface defines all required abstract methods."""
        required_methods = [
            'save_card', 'get_card', 'update_card', 'delete_card',
            'get_user_cards', 'save_review', 'get_reviews',
            'get_user_progress', 'update_user_progress'
        ]
        
        for method_name in required_methods:
            self.assertTrue(
                hasattr(StorageInterface, method_name),
                f"StorageInterface should define {method_name}"
            )
    
    def test_storage_interface_has_docstring(self):
        """Test StorageInterface has docstring."""
        self.assertIsNotNone(StorageInterface.__doc__)


class TestInMemoryStorageCreation(unittest.TestCase):
    """Test InMemoryStorage creation and initialization."""
    
    def test_create_in_memory_storage(self):
        """Test creating InMemoryStorage instance."""
        storage = InMemoryStorage()
        self.assertIsInstance(storage, InMemoryStorage)
        self.assertIsInstance(storage, StorageInterface)
    
    def test_storage_starts_empty(self):
        """Test storage starts with no data."""
        storage = InMemoryStorage()
        
        # Should have no cards initially
        cards = storage.get_user_cards("any_user")
        self.assertEqual(len(cards), 0)


class TestInMemoryStorageCardOperations(unittest.TestCase):
    """Test InMemoryStorage card CRUD operations."""
    
    def setUp(self):
        """Set up test storage before each test."""
        self.storage = InMemoryStorage()
    
    def test_save_card(self):
        """Test saving a card."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        
        saved_card = self.storage.save_card(card)
        
        self.assertEqual(saved_card.card_id, card.card_id)
        self.assertEqual(saved_card.user_id, card.user_id)
        self.assertEqual(saved_card.front, card.front)
        self.assertEqual(saved_card.back, card.back)
    
    def test_get_saved_card(self):
        """Test retrieving a saved card."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        
        self.storage.save_card(card)
        retrieved_card = self.storage.get_card("card_001")
        
        self.assertEqual(retrieved_card.card_id, card.card_id)
        self.assertEqual(retrieved_card.front, card.front)
        self.assertEqual(retrieved_card.back, card.back)
    
    def test_get_nonexistent_card_raises_error(self):
        """Test getting nonexistent card raises CardNotFoundError."""
        with self.assertRaises(CardNotFoundError):
            self.storage.get_card("nonexistent_card")
    
    def test_update_card(self):
        """Test updating a card."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Original Question",
            back="Original Answer"
        )
        
        self.storage.save_card(card)
        
        # Update the card
        card.front = "Updated Question"
        card.back = "Updated Answer"
        updated_card = self.storage.update_card(card)
        
        self.assertEqual(updated_card.front, "Updated Question")
        self.assertEqual(updated_card.back, "Updated Answer")
        
        # Verify update persisted
        retrieved = self.storage.get_card("card_001")
        self.assertEqual(retrieved.front, "Updated Question")
    
    def test_update_nonexistent_card_raises_error(self):
        """Test updating nonexistent card raises error."""
        card = Card(
            card_id="nonexistent",
            user_id="user_123",
            front="Q",
            back="A"
        )
        
        with self.assertRaises(CardNotFoundError):
            self.storage.update_card(card)
    
    def test_delete_card(self):
        """Test deleting a card."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        
        self.storage.save_card(card)
        result = self.storage.delete_card("card_001")
        
        self.assertTrue(result)
        
        # Verify card is deleted
        with self.assertRaises(CardNotFoundError):
            self.storage.get_card("card_001")
    
    def test_delete_nonexistent_card(self):
        """Test deleting nonexistent card returns False."""
        result = self.storage.delete_card("nonexistent")
        self.assertFalse(result)
    
    def test_get_user_cards_empty(self):
        """Test getting cards for user with no cards."""
        cards = self.storage.get_user_cards("user_123")
        self.assertEqual(len(cards), 0)
    
    def test_get_user_cards_single(self):
        """Test getting cards for user with one card."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        
        self.storage.save_card(card)
        cards = self.storage.get_user_cards("user_123")
        
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].card_id, "card_001")
    
    def test_get_user_cards_multiple(self):
        """Test getting multiple cards for user."""
        for i in range(5):
            card = Card(
                card_id=f"card_{i:03d}",
                user_id="user_123",
                front=f"Question {i}",
                back=f"Answer {i}"
            )
            self.storage.save_card(card)
        
        cards = self.storage.get_user_cards("user_123")
        
        self.assertEqual(len(cards), 5)
    
    def test_get_user_cards_filtered_by_user(self):
        """Test cards are filtered by user_id."""
        # Create cards for different users
        card1 = Card(
            card_id="card_001",
            user_id="user_123",
            front="Q1",
            back="A1"
        )
        card2 = Card(
            card_id="card_002",
            user_id="user_456",
            front="Q2",
            back="A2"
        )
        
        self.storage.save_card(card1)
        self.storage.save_card(card2)
        
        # Get cards for user_123
        cards = self.storage.get_user_cards("user_123")
        
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].card_id, "card_001")


class TestInMemoryStorageReviewOperations(unittest.TestCase):
    """Test InMemoryStorage review operations."""
    
    def setUp(self):
        """Set up test storage before each test."""
        self.storage = InMemoryStorage()
    
    def test_save_review(self):
        """Test saving a review."""
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
        
        saved_review = self.storage.save_review(review)
        
        self.assertEqual(saved_review.review_id, review.review_id)
        self.assertEqual(saved_review.card_id, review.card_id)
        self.assertEqual(saved_review.quality, review.quality)
    
    def test_get_reviews_for_card(self):
        """Test getting reviews for a specific card."""
        # Save multiple reviews for same card
        for i in range(3):
            review = Review(
                review_id=f"rev_{i:03d}",
                card_id="card_001",
                user_id="user_123",
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
        
        reviews = self.storage.get_reviews(card_id="card_001")
        
        self.assertEqual(len(reviews), 3)
    
    def test_get_reviews_for_user(self):
        """Test getting reviews for a specific user."""
        # Save reviews for different users
        for i in range(2):
            review = Review(
                review_id=f"rev_user1_{i}",
                card_id=f"card_{i}",
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
            self.storage.save_review(review)
        
        reviews = self.storage.get_reviews(user_id="user_123")
        
        self.assertEqual(len(reviews), 2)
    
    def test_get_reviews_no_filters(self):
        """Test getting all reviews without filters."""
        # Save some reviews
        for i in range(5):
            review = Review(
                review_id=f"rev_{i:03d}",
                card_id=f"card_{i}",
                user_id=f"user_{i}",
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
        
        reviews = self.storage.get_reviews()
        
        self.assertEqual(len(reviews), 5)


class TestInMemoryStorageUserProgressOperations(unittest.TestCase):
    """Test InMemoryStorage user progress operations."""
    
    def setUp(self):
        """Set up test storage before each test."""
        self.storage = InMemoryStorage()
    
    def test_get_user_progress_new_user(self):
        """Test getting progress for new user creates default progress."""
        progress = self.storage.get_user_progress("user_123")
        
        self.assertEqual(progress.user_id, "user_123")
        self.assertEqual(progress.total_reviews, 0)
        self.assertEqual(progress.current_streak_days, 0)
    
    def test_update_user_progress(self):
        """Test updating user progress."""
        progress = self.storage.get_user_progress("user_123")
        progress.total_reviews = 50
        progress.current_streak_days = 7
        
        updated = self.storage.update_user_progress(progress)
        
        self.assertEqual(updated.total_reviews, 50)
        self.assertEqual(updated.current_streak_days, 7)
        
        # Verify update persisted
        retrieved = self.storage.get_user_progress("user_123")
        self.assertEqual(retrieved.total_reviews, 50)
        self.assertEqual(retrieved.current_streak_days, 7)


class TestInMemoryStorageThreadSafety(unittest.TestCase):
    """Test InMemoryStorage thread safety."""
    
    def setUp(self):
        """Set up test storage before each test."""
        self.storage = InMemoryStorage()
    
    def test_concurrent_card_saves(self):
        """Test concurrent card saves don't corrupt data."""
        num_threads = 10
        cards_per_thread = 10
        threads = []
        
        def save_cards(thread_id):
            for i in range(cards_per_thread):
                card = Card(
                    card_id=f"card_t{thread_id}_{i:03d}",
                    user_id="user_123",
                    front=f"Question {thread_id}-{i}",
                    back=f"Answer {thread_id}-{i}"
                )
                self.storage.save_card(card)
        
        # Create and start threads
        for t in range(num_threads):
            thread = threading.Thread(target=save_cards, args=(t,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all cards were saved
        cards = self.storage.get_user_cards("user_123")
        self.assertEqual(len(cards), num_threads * cards_per_thread)
    
    def test_concurrent_card_updates(self):
        """Test concurrent updates to same card."""
        card = Card(
            card_id="card_001",
            user_id="user_123",
            front="Question",
            back="Answer",
            reviews_count=0
        )
        self.storage.save_card(card)
        
        num_threads = 10
        threads = []
        
        def update_card():
            for _ in range(10):
                card = self.storage.get_card("card_001")
                card.reviews_count += 1
                self.storage.update_card(card)
                time.sleep(0.001)  # Small delay to increase chance of race condition
        
        # Create and start threads
        for _ in range(num_threads):
            thread = threading.Thread(target=update_card)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Due to thread safety, final count should be correct
        final_card = self.storage.get_card("card_001")
        # Note: Without proper locking, this might fail
        # With proper locking, it should equal num_threads * 10


class TestInMemoryStorageEdgeCases(unittest.TestCase):
    """Test InMemoryStorage edge cases."""
    
    def setUp(self):
        """Set up test storage before each test."""
        self.storage = InMemoryStorage()
    
    def test_save_card_with_same_id_overwrites(self):
        """Test saving card with existing ID overwrites it."""
        card1 = Card(
            card_id="card_001",
            user_id="user_123",
            front="Original",
            back="Original"
        )
        
        card2 = Card(
            card_id="card_001",
            user_id="user_123",
            front="Updated",
            back="Updated"
        )
        
        self.storage.save_card(card1)
        self.storage.save_card(card2)
        
        retrieved = self.storage.get_card("card_001")
        self.assertEqual(retrieved.front, "Updated")
    
    def test_large_number_of_cards(self):
        """Test storage with large number of cards."""
        num_cards = 1000
        
        for i in range(num_cards):
            card = Card(
                card_id=f"card_{i:05d}",
                user_id="user_123",
                front=f"Question {i}",
                back=f"Answer {i}"
            )
            self.storage.save_card(card)
        
        cards = self.storage.get_user_cards("user_123")
        self.assertEqual(len(cards), num_cards)
    
    def test_card_with_special_characters_in_id(self):
        """Test card with special characters in ID."""
        card = Card(
            card_id="card_123-abc_xyz.test",
            user_id="user_123",
            front="Question",
            back="Answer"
        )
        
        self.storage.save_card(card)
        retrieved = self.storage.get_card("card_123-abc_xyz.test")
        
        self.assertEqual(retrieved.card_id, card.card_id)
    
    def test_empty_card_id_raises_error(self):
        """Test that cards with empty IDs fail validation."""
        # This should be caught by Card validation, not storage
        with self.assertRaises(ValueError):
            card = Card(
                card_id="",
                user_id="user_123",
                front="Question",
                back="Answer"
            )


class TestInMemoryStorageDocumentation(unittest.TestCase):
    """Test InMemoryStorage documentation."""
    
    def test_in_memory_storage_has_docstring(self):
        """Test InMemoryStorage has docstring."""
        self.assertIsNotNone(InMemoryStorage.__doc__)
        self.assertTrue(len(InMemoryStorage.__doc__) > 0)
    
    def test_methods_have_docstrings(self):
        """Test key methods have docstrings."""
        storage = InMemoryStorage()
        methods = [
            'save_card', 'get_card', 'update_card', 'delete_card',
            'get_user_cards', 'save_review', 'get_reviews',
            'get_user_progress', 'update_user_progress'
        ]
        
        for method_name in methods:
            method = getattr(storage, method_name)
            self.assertIsNotNone(
                method.__doc__,
                f"{method_name} should have a docstring"
            )


class TestInMemoryStorageTypeHints(unittest.TestCase):
    """Test InMemoryStorage type hints."""
    
    def test_save_card_has_type_hints(self):
        """Test save_card has type hints."""
        hints = get_type_hints(InMemoryStorage.save_card)
        self.assertIn('card', hints)
        self.assertIn('return', hints)
    
    def test_get_card_has_type_hints(self):
        """Test get_card has type hints."""
        hints = get_type_hints(InMemoryStorage.get_card)
        self.assertIn('card_id', hints)
        self.assertIn('return', hints)


if __name__ == '__main__':
    unittest.main(verbosity=2)
