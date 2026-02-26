"""
Unit Tests — SP-Quiz : CardManager
==========================================

Tests for CardManager CRUD operations and thread safety.

Covers Design Spec Document V1 - §9.3 requirements:
- Full CRUD operations (create, read, update, delete)
- Thread-safe operations
- Batch operations
- Tag-based filtering
- Search functionality
- Error handling
- Validation

Running the tests
-----------------
::

    python -m pytest test_card_manager.py -v
    python -m unittest test_card_manager -v

Dependencies
------------
Python standard library and sp_quiz package.
"""

import unittest
import threading
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.managers.card_manager import CardManager
from sp_quiz.core.card import CardState
from sp_quiz.core.exceptions import (
    CardNotFoundError,
    ValidationError
)
from sp_quiz.storage.memory import InMemoryStorage


class TestCardManagerCreation(unittest.TestCase):
    """Test CardManager initialization."""
    
    def test_create_card_manager_with_storage(self):
        """CardManager requires storage backend."""
        storage = InMemoryStorage()
        manager = CardManager(storage)
        self.assertIsInstance(manager, CardManager)
    
    def test_card_manager_without_storage_raises_error(self):
        """CardManager requires valid storage backend."""
        with self.assertRaises(TypeError):
            CardManager(None)


class TestCardManagerCRUD(unittest.TestCase):
    """Test CardManager CRUD operations."""
    
    def setUp(self):
        """Set up test manager before each test."""
        self.storage = InMemoryStorage()
        self.manager = CardManager(self.storage)
        self.user_id = "test_user_001"
    
    def test_create_card(self):
        """Test creating a new card."""
        card = self.manager.create_card(
            user_id=self.user_id,
            front="What is Python?",
            back="A programming language",
            tags=["programming", "basics"]
        )
        
        self.assertIsNotNone(card.card_id)
        self.assertEqual(card.user_id, self.user_id)
        self.assertEqual(card.front, "What is Python?")
        self.assertEqual(card.back, "A programming language")
        self.assertEqual(card.state, CardState.NEW)
        self.assertIn("programming", card.tags)
    
    def test_create_card_generates_unique_id(self):
        """Each created card should have unique ID."""
        card1 = self.manager.create_card(self.user_id, "Q1", "A1")
        card2 = self.manager.create_card(self.user_id, "Q2", "A2")
        
        self.assertNotEqual(card1.card_id, card2.card_id)
    
    def test_get_card(self):
        """Test retrieving a card by ID."""
        created = self.manager.create_card(self.user_id, "Q", "A")
        retrieved = self.manager.get_card(created.card_id)
        
        self.assertEqual(retrieved.card_id, created.card_id)
        self.assertEqual(retrieved.front, created.front)
    
    def test_get_nonexistent_card_raises_error(self):
        """Getting nonexistent card should raise CardNotFoundError."""
        with self.assertRaises(CardNotFoundError):
            self.manager.get_card("nonexistent_id")
    
    def test_update_card(self):
        """Test updating an existing card."""
        card = self.manager.create_card(self.user_id, "Old Front", "Old Back")
        
        updated = self.manager.update_card(
            card_id=card.card_id,
            front="New Front",
            back="New Back",
            tags=["updated"]
        )
        
        self.assertEqual(updated.front, "New Front")
        self.assertEqual(updated.back, "New Back")
        self.assertIn("updated", updated.tags)
    
    def test_update_card_partial_fields(self):
        """Test updating only specific fields."""
        card = self.manager.create_card(self.user_id, "Q", "A", tags=["original"])
        
        updated = self.manager.update_card(
            card_id=card.card_id,
            front="Updated Question"
        )
        
        self.assertEqual(updated.front, "Updated Question")
        self.assertEqual(updated.back, "A")  # Unchanged
        self.assertIn("original", updated.tags)  # Unchanged
    
    def test_delete_card(self):
        """Test deleting a card."""
        card = self.manager.create_card(self.user_id, "Q", "A")
        
        result = self.manager.delete_card(card.card_id)
        self.assertTrue(result)
        
        with self.assertRaises(CardNotFoundError):
            self.manager.get_card(card.card_id)
    
    def test_delete_nonexistent_card(self):
        """Deleting nonexistent card should return False."""
        result = self.manager.delete_card("nonexistent")
        self.assertFalse(result)


class TestCardManagerValidation(unittest.TestCase):
    """Test CardManager validation logic."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.manager = CardManager(self.storage)
        self.user_id = "test_user"
    
    def test_create_card_empty_front_raises_error(self):
        """Creating card with empty front should raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.manager.create_card(self.user_id, "", "Answer")
    
    def test_create_card_empty_back_raises_error(self):
        """Creating card with empty back should raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.manager.create_card(self.user_id, "Question", "")
    
    def test_create_card_whitespace_only_raises_error(self):
        """Creating card with whitespace-only content should fail."""
        with self.assertRaises(ValidationError):
            self.manager.create_card(self.user_id, "   ", "   ")
    
    def test_create_card_invalid_user_id_raises_error(self):
        """Creating card with empty user_id should raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.manager.create_card("", "Q", "A")


class TestCardManagerBatchOperations(unittest.TestCase):
    """Test CardManager batch operations."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.manager = CardManager(self.storage)
        self.user_id = "batch_user"
    
    def test_create_cards_batch(self):
        """Test creating multiple cards at once."""
        cards_data = [
            {"front": "Q1", "back": "A1"},
            {"front": "Q2", "back": "A2"},
            {"front": "Q3", "back": "A3"},
        ]
        
        created_cards = self.manager.create_cards_batch(
            self.user_id, cards_data
        )
        
        self.assertEqual(len(created_cards), 3)
        self.assertEqual(created_cards[0].front, "Q1")
        self.assertEqual(created_cards[2].front, "Q3")
    
    def test_get_user_cards(self):
        """Test retrieving all cards for a user."""
        # Create cards for user
        for i in range(5):
            self.manager.create_card(self.user_id, f"Q{i}", f"A{i}")
        
        cards = self.manager.get_user_cards(self.user_id)
        
        self.assertEqual(len(cards), 5)
    
    def test_get_user_cards_empty(self):
        """Getting cards for user with no cards returns empty list."""
        cards = self.manager.get_user_cards("new_user")
        self.assertEqual(len(cards), 0)
    
    def test_delete_user_cards(self):
        """Test deleting all cards for a user."""
        # Create cards
        for i in range(3):
            self.manager.create_card(self.user_id, f"Q{i}", f"A{i}")
        
        count = self.manager.delete_user_cards(self.user_id)
        
        self.assertEqual(count, 3)
        self.assertEqual(len(self.manager.get_user_cards(self.user_id)), 0)


class TestCardManagerFiltering(unittest.TestCase):
    """Test CardManager filtering capabilities."""
    
    def setUp(self):
        """Set up test manager with test data."""
        self.storage = InMemoryStorage()
        self.manager = CardManager(self.storage)
        self.user_id = "filter_user"
        
        # Create cards with different states and tags
        self.manager.create_card(self.user_id, "Q1", "A1", tags=["python", "basics"])
        self.manager.create_card(self.user_id, "Q2", "A2", tags=["python", "advanced"])
        self.manager.create_card(self.user_id, "Q3", "A3", tags=["java", "basics"])
    
    def test_filter_by_tags(self):
        """Test filtering cards by tags."""
        python_cards = self.manager.get_cards_by_tags(
            self.user_id, ["python"]
        )
        
        self.assertEqual(len(python_cards), 2)
    
    def test_filter_by_multiple_tags(self):
        """Test filtering by multiple tags (AND logic)."""
        cards = self.manager.get_cards_by_tags(
            self.user_id, ["python", "basics"]
        )
        
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].front, "Q1")
    
    def test_filter_by_state(self):
        """Test filtering cards by state."""
        # Update one card to LEARNING state
        cards = self.manager.get_user_cards(self.user_id)
        self.manager.update_card(cards[0].card_id, state=CardState.LEARNING)
        
        new_cards = self.manager.get_cards_by_state(
            self.user_id, CardState.NEW
        )
        learning_cards = self.manager.get_cards_by_state(
            self.user_id, CardState.LEARNING
        )
        
        self.assertEqual(len(new_cards), 2)
        self.assertEqual(len(learning_cards), 1)
    
    def test_filter_by_due_date(self):
        """Test filtering cards by due date."""
        # Create cards with different due dates
        now = datetime.utcnow()
        
        card1 = self.manager.create_card(self.user_id, "Overdue", "A")
        self.manager.update_card(
            card1.card_id,
            due_datetime=now - timedelta(days=1)
        )
        
        card2 = self.manager.create_card(self.user_id, "Due Soon", "A")
        self.manager.update_card(
            card2.card_id,
            due_datetime=now + timedelta(hours=1)
        )
        
        due_cards = self.manager.get_due_cards(self.user_id)
        
        self.assertGreaterEqual(len(due_cards), 1)


class TestCardManagerSearch(unittest.TestCase):
    """Test CardManager search functionality."""
    
    def setUp(self):
        """Set up test manager with searchable data."""
        self.storage = InMemoryStorage()
        self.manager = CardManager(self.storage)
        self.user_id = "search_user"
        
        self.manager.create_card(self.user_id, "What is Python?", "Programming language")
        self.manager.create_card(self.user_id, "What is Java?", "Programming language")
        self.manager.create_card(self.user_id, "Capital of France?", "Paris")
    
    def test_search_in_front(self):
        """Test searching in card front text."""
        results = self.manager.search_cards(self.user_id, "Python")
        
        self.assertEqual(len(results), 1)
        self.assertIn("Python", results[0].front)
    
    def test_search_in_back(self):
        """Test searching in card back text."""
        results = self.manager.search_cards(self.user_id, "Paris")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].back, "Paris")
    
    def test_search_case_insensitive(self):
        """Search should be case-insensitive."""
        results = self.manager.search_cards(self.user_id, "python")
        
        self.assertEqual(len(results), 1)
    
    def test_search_multiple_results(self):
        """Search can return multiple results."""
        results = self.manager.search_cards(self.user_id, "Programming")
        
        self.assertEqual(len(results), 2)
    
    def test_search_no_results(self):
        """Search with no matches returns empty list."""
        results = self.manager.search_cards(self.user_id, "nonexistent")
        
        self.assertEqual(len(results), 0)


class TestCardManagerThreadSafety(unittest.TestCase):
    """Test CardManager thread safety."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.manager = CardManager(self.storage)
        self.user_id = "thread_user"
    
    def test_concurrent_card_creation(self):
        """Test creating cards concurrently from multiple threads."""
        num_threads = 10
        cards_per_thread = 10
        created_cards = []
        lock = threading.Lock()
        
        def create_cards(thread_id):
            for i in range(cards_per_thread):
                card = self.manager.create_card(
                    self.user_id,
                    f"T{thread_id}_Q{i}",
                    f"T{thread_id}_A{i}"
                )
                with lock:
                    created_cards.append(card)
        
        threads = [
            threading.Thread(target=create_cards, args=(t,))
            for t in range(num_threads)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All cards should be created
        self.assertEqual(len(created_cards), num_threads * cards_per_thread)
        
        # All card IDs should be unique
        card_ids = [c.card_id for c in created_cards]
        self.assertEqual(len(card_ids), len(set(card_ids)))
    
    def test_concurrent_read_write(self):
        """Test concurrent reading and writing."""
        card = self.manager.create_card(self.user_id, "Q", "A")
        
        def update_card():
            for _ in range(10):
                self.manager.update_card(
                    card.card_id,
                    front="Updated"
                )
        
        def read_card():
            for _ in range(10):
                self.manager.get_card(card.card_id)
        
        threads = [
            threading.Thread(target=update_card),
            threading.Thread(target=read_card),
            threading.Thread(target=update_card),
            threading.Thread(target=read_card),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not crash
        final_card = self.manager.get_card(card.card_id)
        self.assertIsNotNone(final_card)


class TestCardManagerStatistics(unittest.TestCase):
    """Test CardManager statistics methods."""
    
    def setUp(self):
        """Set up test manager with data."""
        self.storage = InMemoryStorage()
        self.manager = CardManager(self.storage)
        self.user_id = "stats_user"
        
        # Create cards in different states
        for i in range(3):
            self.manager.create_card(self.user_id, f"New{i}", f"A{i}")
        
        for i in range(2):
            card = self.manager.create_card(self.user_id, f"Learning{i}", f"A{i}")
            self.manager.update_card(card.card_id, state=CardState.LEARNING)
        
        for i in range(5):
            card = self.manager.create_card(self.user_id, f"Review{i}", f"A{i}")
            self.manager.update_card(card.card_id, state=CardState.REVIEW)
    
    def test_get_card_count_by_state(self):
        """Test getting card counts by state."""
        counts = self.manager.get_card_counts_by_state(self.user_id)
        
        self.assertEqual(counts[CardState.NEW], 3)
        self.assertEqual(counts[CardState.LEARNING], 2)
        self.assertEqual(counts[CardState.REVIEW], 5)
    
    def test_get_total_card_count(self):
        """Test getting total card count for user."""
        total = self.manager.get_total_card_count(self.user_id)
        
        self.assertEqual(total, 10)


class TestCardManagerEdgeCases(unittest.TestCase):
    """Test CardManager edge cases and error conditions."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.manager = CardManager(self.storage)
        self.user_id = "edge_user"
    
    def test_update_nonexistent_card(self):
        """Updating nonexistent card should raise error."""
        with self.assertRaises(CardNotFoundError):
            self.manager.update_card("nonexistent", front="New")
    
    def test_create_card_with_metadata(self):
        """Test creating card with custom metadata."""
        card = self.manager.create_card(
            self.user_id, "Q", "A",
            metadata={"difficulty": "hard", "source": "textbook"}
        )
        
        self.assertEqual(card.metadata["difficulty"], "hard")
        self.assertEqual(card.metadata["source"], "textbook")
    
    def test_create_card_very_long_content(self):
        """Test creating card with very long content."""
        long_front = "Q" * 10000
        long_back = "A" * 10000
        
        card = self.manager.create_card(self.user_id, long_front, long_back)
        
        self.assertEqual(len(card.front), 10000)
        self.assertEqual(len(card.back), 10000)
    
    def test_special_characters_in_content(self):
        """Test cards with special characters."""
        special_front = "What is λ-calculus?"
        special_back = "A formal system: ∀x∃y(x ≤ y)"
        
        card = self.manager.create_card(
            self.user_id, special_front, special_back
        )
        
        self.assertEqual(card.front, special_front)
        self.assertEqual(card.back, special_back)


if __name__ == "__main__":
    unittest.main(verbosity=2)
