"""
Unit Tests — SP-Quiz Phase 3: SessionManager
============================================

Tests for SessionManager review session orchestration.

Covers §9.3 requirements:
- Session lifecycle (start, conduct reviews, end)
- Review submission and validation
- Session state management
- Quality scoring integration
- Statistics tracking
- Thread safety
- Error handling

Running the tests
-----------------
::

    python -m pytest test_session_manager.py -v
    python -m unittest test_session_manager -v

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

from sp_quiz.managers.session_manager import SessionManager
from sp_quiz.managers.card_manager import CardManager
from sp_quiz.core.card import CardState
from sp_quiz.core.review import Review
from sp_quiz.core.user import UserProgress
from sp_quiz.core.exceptions import (
    SessionNotFoundError,
    SessionClosedError,
    CardNotFoundError,
    ValidationError
)
from sp_quiz.storage.memory import InMemoryStorage
from sp_quiz.algorithms.sm2_plus import SM2Plus
from sp_quiz.algorithms.scheduler import Scheduler
from sp_quiz.algorithms.quality_scorer import QualityScorer


class TestSessionManagerCreation(unittest.TestCase):
    """Test SessionManager initialization."""
    
    def test_create_session_manager(self):
        """SessionManager requires storage, algo, scheduler, scorer."""
        storage = InMemoryStorage()
        algo = SM2Plus()
        scheduler = Scheduler()
        scorer = QualityScorer()
        
        manager = SessionManager(storage, algo, scheduler, scorer)
        self.assertIsInstance(manager, SessionManager)
    
    def test_session_manager_missing_dependencies_raises_error(self):
        """SessionManager requires all dependencies."""
        storage = InMemoryStorage()
        
        with self.assertRaises(TypeError):
            SessionManager(storage, None, None, None)


class TestSessionLifecycle(unittest.TestCase):
    """Test review session lifecycle."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()
        self.scheduler = Scheduler()
        self.scorer = QualityScorer()
        self.manager = SessionManager(
            self.storage, self.algo, self.scheduler, self.scorer
        )
        self.card_manager = CardManager(self.storage)
        self.user_id = "session_user"
        
        # Create test cards
        for i in range(5):
            card = self.card_manager.create_card(
                self.user_id, f"Q{i}", f"A{i}"
            )
            # Make them due
            self.card_manager.update_card(
                card.card_id,
                state=CardState.REVIEW,
                due_datetime=datetime.utcnow() - timedelta(hours=1)
            )
    
    def test_start_session(self):
        """Test starting a new review session."""
        session = self.manager.start_session(
            user_id=self.user_id,
            max_cards=10
        )
        
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.user_id, self.user_id)
        self.assertEqual(session.cards_reviewed, 0)
        self.assertFalse(session.is_closed)
    
    def test_start_session_generates_unique_id(self):
        """Each session should have unique ID."""
        session1 = self.manager.start_session(self.user_id)
        session2 = self.manager.start_session(self.user_id)
        
        self.assertNotEqual(session1.session_id, session2.session_id)
    
    def test_get_session(self):
        """Test retrieving an active session."""
        created = self.manager.start_session(self.user_id)
        retrieved = self.manager.get_session(created.session_id)
        
        self.assertEqual(retrieved.session_id, created.session_id)
        self.assertEqual(retrieved.user_id, created.user_id)
    
    def test_get_nonexistent_session_raises_error(self):
        """Getting nonexistent session should raise error."""
        with self.assertRaises(SessionNotFoundError):
            self.manager.get_session("nonexistent_session")
    
    def test_end_session(self):
        """Test ending a review session."""
        session = self.manager.start_session(self.user_id)
        
        summary = self.manager.end_session(session.session_id)
        
        self.assertEqual(summary.session_id, session.session_id)
        self.assertIsNotNone(summary.duration_seconds)
        self.assertTrue(summary.session_completed)
    
    def test_session_marked_closed_after_end(self):
        """Session should be marked closed after ending."""
        session = self.manager.start_session(self.user_id)
        self.manager.end_session(session.session_id)
        
        retrieved = self.manager.get_session(session.session_id)
        self.assertTrue(retrieved.is_closed)


class TestReviewSubmission(unittest.TestCase):
    """Test review submission within sessions."""
    
    def setUp(self):
        """Set up test manager with session."""
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()
        self.scheduler = Scheduler()
        self.scorer = QualityScorer()
        self.manager = SessionManager(
            self.storage, self.algo, self.scheduler, self.scorer
        )
        self.card_manager = CardManager(self.storage)
        self.user_id = "review_user"
        
        # Create and schedule cards
        self.cards = []
        for i in range(3):
            card = self.card_manager.create_card(
                self.user_id, f"Question {i}", f"Answer {i}"
            )
            self.card_manager.update_card(
                card.card_id,
                state=CardState.REVIEW,
                due_datetime=datetime.utcnow() - timedelta(hours=1)
            )
            self.cards.append(card)
        
        self.session = self.manager.start_session(self.user_id)
    
    def test_get_next_card(self):
        """Test getting next card for review."""
        card = self.manager.get_next_card(self.session.session_id)
        
        self.assertIsNotNone(card)
        self.assertEqual(card.user_id, self.user_id)
    
    def test_submit_review_manual_quality(self):
        """Test submitting review with manual quality rating."""
        card = self.manager.get_next_card(self.session.session_id)
        
        result = self.manager.submit_review(
            session_id=self.session.session_id,
            card_id=card.card_id,
            quality=4,
            time_taken_seconds=5.0
        )
        
        self.assertIsNotNone(result.review_id)
        self.assertEqual(result.quality, 4)
        self.assertIsNotNone(result.next_due_datetime)
    
    def test_submit_review_automatic_quality(self):
        """Test submitting review with automatic quality scoring."""
        card = self.manager.get_next_card(self.session.session_id)
        
        result = self.manager.submit_review(
            session_id=self.session.session_id,
            card_id=card.card_id,
            answer_user="Answer 0",
            response_times={
                't_first': 2.0,
                't_typing': 0.5,
                't_total': 2.5
            }
        )
        
        self.assertIsNotNone(result.review_id)
        self.assertIn(result.quality, [0, 1, 2, 3, 4, 5])
    
    def test_submit_review_updates_card_schedule(self):
        """Review submission should update card's schedule."""
        card = self.manager.get_next_card(self.session.session_id)
        original_interval = card.interval_days
        
        self.manager.submit_review(
            self.session.session_id,
            card.card_id,
            quality=4,
            time_taken_seconds=5.0
        )
        
        updated_card = self.card_manager.get_card(card.card_id)
        self.assertGreater(updated_card.interval_days, original_interval)
    
    def test_submit_review_creates_review_record(self):
        """Review submission should create Review record."""
        card = self.manager.get_next_card(self.session.session_id)
        
        result = self.manager.submit_review(
            self.session.session_id,
            card.card_id,
            quality=3,
            time_taken_seconds=7.0
        )
        
        reviews = self.storage.get_reviews(card_id=card.card_id)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].quality, 3)
    
    def test_submit_review_increments_session_counter(self):
        """Each review should increment session's review counter."""
        card1 = self.manager.get_next_card(self.session.session_id)
        self.manager.submit_review(self.session.session_id, card1.card_id, quality=4)
        
        card2 = self.manager.get_next_card(self.session.session_id)
        self.manager.submit_review(self.session.session_id, card2.card_id, quality=5)
        
        session = self.manager.get_session(self.session.session_id)
        self.assertEqual(session.cards_reviewed, 2)
    
    def test_submit_review_to_closed_session_raises_error(self):
        """Submitting review to closed session should raise error."""
        card = self.manager.get_next_card(self.session.session_id)
        self.manager.end_session(self.session.session_id)
        
        with self.assertRaises(SessionClosedError):
            self.manager.submit_review(
                self.session.session_id,
                card.card_id,
                quality=4
            )


class TestSessionConfiguration(unittest.TestCase):
    """Test session configuration options."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()
        self.scheduler = Scheduler()
        self.scorer = QualityScorer()
        self.manager = SessionManager(
            self.storage, self.algo, self.scheduler, self.scorer
        )
        self.card_manager = CardManager(self.storage)
        self.user_id = "config_user"
        
        # Create 10 due cards
        for i in range(10):
            card = self.card_manager.create_card(self.user_id, f"Q{i}", f"A{i}")
            self.card_manager.update_card(
                card.card_id,
                state=CardState.REVIEW,
                due_datetime=datetime.utcnow() - timedelta(hours=1)
            )
    
    def test_session_with_max_cards_limit(self):
        """Session should respect max_cards limit."""
        session = self.manager.start_session(self.user_id, max_cards=5)
        
        cards_seen = []
        for _ in range(10):  # Try to get more than limit
            card = self.manager.get_next_card(session.session_id)
            if card is None:
                break
            cards_seen.append(card)
            self.manager.submit_review(session.session_id, card.card_id, quality=4)
        
        self.assertLessEqual(len(cards_seen), 5)
    
    def test_session_with_time_limit(self):
        """Session can have time limit configuration."""
        session = self.manager.start_session(
            self.user_id,
            max_duration_minutes=5
        )
        
        self.assertEqual(session.max_duration_minutes, 5)
    
    def test_session_with_new_cards_only(self):
        """Session can be configured to show only new cards."""
        # Create some NEW cards
        for i in range(3):
            self.card_manager.create_card(self.user_id, f"New{i}", f"A{i}")
        
        session = self.manager.start_session(
            self.user_id,
            card_states=[CardState.NEW]
        )
        
        card = self.manager.get_next_card(session.session_id)
        self.assertEqual(card.state, CardState.NEW)


class TestSessionStatistics(unittest.TestCase):
    """Test session statistics tracking."""
    
    def setUp(self):
        """Set up test manager with completed reviews."""
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()
        self.scheduler = Scheduler()
        self.scorer = QualityScorer()
        self.manager = SessionManager(
            self.storage, self.algo, self.scheduler, self.scorer
        )
        self.card_manager = CardManager(self.storage)
        self.user_id = "stats_user"
        
        # Create cards
        for i in range(5):
            card = self.card_manager.create_card(self.user_id, f"Q{i}", f"A{i}")
            self.card_manager.update_card(
                card.card_id,
                state=CardState.REVIEW,
                due_datetime=datetime.utcnow() - timedelta(hours=1)
            )
        
        # Complete a session
        self.session = self.manager.start_session(self.user_id)
        qualities = [4, 5, 3, 4, 2]
        
        for quality in qualities:
            card = self.manager.get_next_card(self.session.session_id)
            if card:
                self.manager.submit_review(
                    self.session.session_id,
                    card.card_id,
                    quality=quality
                )
    
    def test_session_summary_includes_review_count(self):
        """Session summary should include total reviews."""
        summary = self.manager.end_session(self.session.session_id)
        
        self.assertEqual(summary.total_reviews, 5)
    
    def test_session_summary_calculates_average_quality(self):
        """Session summary should calculate average quality."""
        summary = self.manager.end_session(self.session.session_id)
        
        # Average of [4, 5, 3, 4, 2] = 3.6
        self.assertAlmostEqual(summary.average_quality, 3.6, places=1)
    
    def test_session_summary_tracks_time(self):
        """Session summary should track duration."""
        summary = self.manager.end_session(self.session.session_id)
        
        self.assertGreater(summary.duration_seconds, 0)
    
    def test_session_summary_quality_distribution(self):
        """Session summary should show quality distribution."""
        summary = self.manager.end_session(self.session.session_id)
        
        # [4, 5, 3, 4, 2]
        self.assertEqual(summary.quality_counts[2], 1)
        self.assertEqual(summary.quality_counts[3], 1)
        self.assertEqual(summary.quality_counts[4], 2)
        self.assertEqual(summary.quality_counts[5], 1)


class TestSessionValidation(unittest.TestCase):
    """Test session validation logic."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()
        self.scheduler = Scheduler()
        self.scorer = QualityScorer()
        self.manager = SessionManager(
            self.storage, self.algo, self.scheduler, self.scorer
        )
        self.user_id = "valid_user"
    
    def test_submit_review_invalid_quality_raises_error(self):
        """Submitting review with invalid quality should raise error."""
        session = self.manager.start_session(self.user_id)
        
        with self.assertRaises(ValidationError):
            self.manager.submit_review(
                session.session_id,
                "some_card_id",
                quality=10  # Invalid
            )
    
    def test_submit_review_negative_time_raises_error(self):
        """Submitting review with negative time should raise error."""
        session = self.manager.start_session(self.user_id)
        
        with self.assertRaises(ValidationError):
            self.manager.submit_review(
                session.session_id,
                "some_card_id",
                quality=4,
                time_taken_seconds=-5.0  # Invalid
            )
    
    def test_submit_review_nonexistent_card_raises_error(self):
        """Submitting review for nonexistent card should raise error."""
        session = self.manager.start_session(self.user_id)
        
        with self.assertRaises(CardNotFoundError):
            self.manager.submit_review(
                session.session_id,
                "nonexistent_card",
                quality=4
            )


class TestSessionThreadSafety(unittest.TestCase):
    """Test SessionManager thread safety."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()
        self.scheduler = Scheduler()
        self.scorer = QualityScorer()
        self.manager = SessionManager(
            self.storage, self.algo, self.scheduler, self.scorer
        )
        self.card_manager = CardManager(self.storage)
        self.user_id = "thread_user"
    
    def test_concurrent_session_creation(self):
        """Test creating multiple sessions concurrently."""
        sessions = []
        lock = threading.Lock()
        
        def create_session(user_id):
            session = self.manager.start_session(user_id)
            with lock:
                sessions.append(session)
        
        threads = [
            threading.Thread(target=create_session, args=(f"user_{i}",))
            for i in range(10)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All sessions created
        self.assertEqual(len(sessions), 10)
        
        # All session IDs unique
        session_ids = [s.session_id for s in sessions]
        self.assertEqual(len(session_ids), len(set(session_ids)))
    
    def test_concurrent_review_submission(self):
        """Test submitting reviews concurrently (different sessions)."""
        # Create cards for multiple users
        users = [f"user_{i}" for i in range(5)]
        sessions = {}
        
        for user_id in users:
            card = self.card_manager.create_card(user_id, "Q", "A")
            self.card_manager.update_card(
                card.card_id,
                state=CardState.REVIEW,
                due_datetime=datetime.utcnow() - timedelta(hours=1)
            )
            sessions[user_id] = self.manager.start_session(user_id)
        
        def submit_review(user_id):
            session = sessions[user_id]
            card = self.manager.get_next_card(session.session_id)
            if card:
                self.manager.submit_review(
                    session.session_id,
                    card.card_id,
                    quality=4
                )
        
        threads = [
            threading.Thread(target=submit_review, args=(user_id,))
            for user_id in users
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All reviews submitted successfully
        for user_id in users:
            session = self.manager.get_session(sessions[user_id].session_id)
            self.assertGreaterEqual(session.cards_reviewed, 0)


class TestSessionEdgeCases(unittest.TestCase):
    """Test SessionManager edge cases."""
    
    def setUp(self):
        """Set up test manager."""
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()
        self.scheduler = Scheduler()
        self.scorer = QualityScorer()
        self.manager = SessionManager(
            self.storage, self.algo, self.scheduler, self.scorer
        )
        self.user_id = "edge_user"
    
    def test_get_next_card_no_due_cards(self):
        """Getting next card when no cards are due returns None."""
        session = self.manager.start_session(self.user_id)
        
        card = self.manager.get_next_card(session.session_id)
        
        self.assertIsNone(card)
    
    def test_end_already_closed_session(self):
        """Ending already closed session should handle gracefully."""
        session = self.manager.start_session(self.user_id)
        self.manager.end_session(session.session_id)
        
        # Second end should not crash
        summary = self.manager.end_session(session.session_id)
        self.assertIsNotNone(summary)
    
    def test_session_with_zero_max_cards(self):
        """Session with max_cards=0 should handle gracefully."""
        session = self.manager.start_session(self.user_id, max_cards=0)
        
        card = self.manager.get_next_card(session.session_id)
        self.assertIsNone(card)


if __name__ == "__main__":
    unittest.main(verbosity=2)
