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
                due_datetime_after=datetime.utcnow() + timedelta(days=interval_after)
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
                    due_datetime_after=datetime.utcnow()
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
                due_datetime_after=datetime.utcnow()
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
            due_datetime_after=datetime.utcnow() + timedelta(minutes=1)
        )
        self.storage.save_review(review)
        
        # 5. Update card state
        first_card.state = CardState.LEARNING
        first_card.interval_days = 1.0
        first_card.reviews_count = 1
        first_card.last_reviewed_at = datetime.utcnow()
        self.storage.update_card(first_card)
        
        # 6. Update user progress
        progress.total_reviews = 1
        progress.reviews_today = 1
        progress.successful_reviews = 1
        progress.new_cards_count = cards_to_add - 1
        progress.learning_cards_count = 1
        progress.current_streak_days = 1
        progress.last_review_date = datetime.utcnow()
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
                due_datetime_after=datetime.utcnow() + timedelta(days=interval_after)
            )
            self.storage.save_review(review)
            
            # Update card
            card = self.storage.get_card(card_id)
            card.state = state_after
            card.interval_days = interval_after
            card.reviews_count += 1
            card.last_reviewed_at = datetime.utcnow()
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
                due_datetime_after=datetime.utcnow()
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


"""
Phase 2 Integration Tests
--------------------------
Covers §8.2 requirements:
  - test_complete_card_lifecycle  (full NEW→LEARNING→REVIEW→lapse loop)
  - Algorithm ↔ Storage round-trip (ScheduleUpdate is persisted correctly)
  - Scheduler ↔ Storage (due cards retrieved in correct priority order)
  - Multi-card session ordering through the Scheduler
  - Adaptive difficulty integration with review history

These tests verify that the Phase 2 algorithm components (SM2Plus, Scheduler)
interact correctly with the Phase 1 data models (Card, Review, InMemoryStorage).
"""

from sp_quiz.algorithms.sm2_plus import SM2Plus
from sp_quiz.algorithms.scheduler import Scheduler


# ─────────────────────────────────────────────────────────────────────────────
# Helper used across Phase 2 integration tests
# ─────────────────────────────────────────────────────────────────────────────

def _review_card_with_algo(
    storage,
    algo: "SM2Plus",
    card: "Card",
    quality: int,
    session_id: str,
    review_id: str,
) -> tuple:
    """
    Apply the SM2+ algorithm to *card*, persist both the updated card and a
    new Review record, then return (updated_card, ScheduleUpdate).

    This helper is the integration seam: the algorithm transforms card state,
    and the result is immediately persisted through InMemoryStorage.
    """
    state_before = card.state
    ef_before = card.ease_factor
    interval_before = card.interval_days

    update = algo.calculate_next_interval(card, quality=quality)

    # Persist the ScheduleUpdate back onto the card
    card.state = update.new_state
    card.ease_factor = update.new_ease_factor
    card.interval_days = update.interval_days
    card.learning_step = update.new_learning_step
    card.due_datetime = update.next_due
    card.reviews_count += 1
    card.lapses_count = update.new_lapses_count
    card.last_reviewed_at = datetime.utcnow()

    storage.update_card(card)

    review = Review(
        review_id=review_id,
        card_id=card.card_id,
        user_id=card.user_id,
        session_id=session_id,
        quality=quality,
        time_taken_seconds=5.0,
        state_before=state_before,
        interval_before=interval_before,
        ease_factor_before=ef_before,
        state_after=update.new_state,
        interval_after=update.interval_days,
        ease_factor_after=update.new_ease_factor,
        due_datetime_after=update.next_due,
    )
    storage.save_review(review)

    return storage.get_card(card.card_id), update


# ─────────────────────────────────────────────────────────────────────────────
# Integration Test Classes (Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

class TestAlgorithmStorageIntegration(unittest.TestCase):
    """
    Verify that SM-2+ algorithm results are correctly round-tripped
    through InMemoryStorage.

    What to look out for
    --------------------
    - ScheduleUpdate fields (interval, EF, state, learning_step) must survive
      a write-then-read cycle unchanged.
    - Review records must faithfully capture the before/after snapshot.
    - Repeated lapses must accumulate correctly in lapses_count.
    """

    def setUp(self):
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()

    def test_schedule_update_persisted_correctly(self):
        """
        After a successful review the updated card retrieved from storage
        must match the ScheduleUpdate produced by the algorithm exactly.
        """
        card = Card(
            card_id="persist_001",
            user_id="user_p",
            front="Q",
            back="A",
            state=CardState.NEW,
            interval_days=0.0,
            ease_factor=2.5,
            learning_step=0,
        )
        self.storage.save_card(card)

        updated_card, update = _review_card_with_algo(
            self.storage, self.algo, card, quality=4,
            session_id="s1", review_id="r1"
        )

        self.assertEqual(updated_card.state, update.new_state)
        self.assertAlmostEqual(updated_card.ease_factor, update.new_ease_factor, places=6)
        self.assertAlmostEqual(updated_card.interval_days, update.interval_days, places=6)
        self.assertEqual(updated_card.learning_step, update.new_learning_step)

    def test_review_record_captures_before_and_after(self):
        """
        The Review saved to storage must accurately record the card's state
        BEFORE and AFTER the algorithm ran.
        """
        card = Card(
            card_id="snap_001",
            user_id="user_s",
            front="Q",
            back="A",
            state=CardState.REVIEW,
            interval_days=5.0,
            ease_factor=2.3,
        )
        self.storage.save_card(card)

        ef_before = card.ease_factor
        interval_before = card.interval_days

        _review_card_with_algo(
            self.storage, self.algo, card, quality=5,
            session_id="s2", review_id="r2"
        )

        reviews = self.storage.get_reviews(card_id="snap_001")
        self.assertEqual(len(reviews), 1)

        r = reviews[0]
        self.assertAlmostEqual(r.ease_factor_before, ef_before, places=6)
        self.assertAlmostEqual(r.interval_before, interval_before, places=6)
        # After-values must differ (q=5 should increase both)
        self.assertGreater(r.interval_after, interval_before)

    def test_full_learning_to_review_lifecycle_with_algorithm(self):
        """
        End-to-end lifecycle:
            NEW  →  LEARNING (step 0→1, q=4)
                 →  LEARNING (step 1→2, q=4)
                 →  REVIEW   (step 2 → graduation, q=4)
                 →  REVIEW   (interval growth, q=4)
                 →  RELEARNING (lapse, q=1)
                 →  REVIEW   (recovery, q=4)

        Verifies §8.2 test_complete_card_lifecycle spec requirement.
        """
        card = Card(
            card_id="lifecycle_001",
            user_id="user_lc",
            front="Q",
            back="A",
            state=CardState.NEW,
            interval_days=0.0,
            ease_factor=2.5,
            learning_step=0,
        )
        self.storage.save_card(card)

        reviews_sequence = [
            # (quality, expected_state_after)
            (4, CardState.LEARNING),    # step 0 → 1
            (4, CardState.LEARNING),    # step 1 → 2
            (4, CardState.REVIEW),      # graduation
            (4, CardState.REVIEW),      # interval grows
            (1, CardState.RELEARNING),  # lapse
            (4, CardState.REVIEW),      # recovery
        ]

        for idx, (quality, expected_state) in enumerate(reviews_sequence):
            card = self.storage.get_card("lifecycle_001")
            card, update = _review_card_with_algo(
                self.storage, self.algo, card, quality=quality,
                session_id="lc_session", review_id=f"lc_r{idx}"
            )
            self.assertEqual(
                card.state, expected_state,
                msg=f"Step {idx}: q={quality}, expected {expected_state}, got {card.state}",
            )

        # Verify complete review history
        reviews = self.storage.get_reviews(card_id="lifecycle_001")
        self.assertEqual(len(reviews), len(reviews_sequence))

    def test_lapse_count_accumulates_correctly(self):
        """
        Three lapses on the same card must result in lapses_count == 3.
        """
        card = Card(
            card_id="lapse_acc",
            user_id="user_l",
            front="Q",
            back="A",
            state=CardState.REVIEW,
            interval_days=10.0,
            ease_factor=2.5,
            lapses_count=0,
        )
        self.storage.save_card(card)

        for i in range(3):
            card = self.storage.get_card("lapse_acc")
            # Force back to REVIEW if it went to RELEARNING so we can lapse again
            if card.state == CardState.RELEARNING:
                card.state = CardState.REVIEW
                card.interval_days = 10.0
                self.storage.update_card(card)
                card = self.storage.get_card("lapse_acc")

            card, _ = _review_card_with_algo(
                self.storage, self.algo, card, quality=0,
                session_id="lapse_sess", review_id=f"l_r{i}"
            )

        final_card = self.storage.get_card("lapse_acc")
        self.assertEqual(final_card.lapses_count, 3)


class TestSchedulerStorageIntegration(unittest.TestCase):
    """
    Verify that the Scheduler correctly integrates with InMemoryStorage
    to produce a well-ordered review queue from real Card objects.

    What to look out for
    --------------------
    - Overdue cards must always appear in the Scheduler result before future cards.
    - After a review (algorithm updates due_datetime), the Scheduler must reflect
      the new schedule when next polled.
    - Multi-user isolation must be maintained in the Scheduler when filtering
      by user_id.
    """

    def setUp(self):
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()
        self.sched = Scheduler()

    def _load_cards_to_scheduler(self, user_id: str, n: int, days_overdue: float = -1.0):
        """Create n cards in storage and add them to the scheduler."""
        for i in range(n):
            card = Card(
                card_id=f"{user_id}_card_{i}",
                user_id=user_id,
                front=f"Q{i}",
                back=f"A{i}",
                state=CardState.REVIEW,
                interval_days=1.0,
                ease_factor=2.5,
                due_datetime=datetime.utcnow() + timedelta(days=days_overdue),
            )
            self.storage.save_card(card)
            self.sched.add_card(card)

    def test_scheduler_returns_overdue_cards_before_future(self):
        """
        5 overdue cards + 5 future cards → get_due_cards returns exactly 5
        and they are ordered earliest-due-first.
        """
        user_id = "sched_user"
        # 5 overdue (different overdue amounts)
        for i in range(5):
            card = Card(
                card_id=f"overdue_{i}",
                user_id=user_id,
                front="Q",
                back="A",
                state=CardState.REVIEW,
                interval_days=1.0,
                ease_factor=2.5,
                due_datetime=datetime.utcnow() - timedelta(days=i + 1),
            )
            self.storage.save_card(card)
            self.sched.add_card(card)

        # 5 future
        for i in range(5):
            card = Card(
                card_id=f"future_{i}",
                user_id=user_id,
                front="Q",
                back="A",
                state=CardState.REVIEW,
                interval_days=1.0,
                ease_factor=2.5,
                due_datetime=datetime.utcnow() + timedelta(days=i + 1),
            )
            self.storage.save_card(card)
            self.sched.add_card(card)

        due = self.sched.get_due_cards(reference_time=datetime.utcnow())
        self.assertEqual(len(due), 5)

        # Confirm ordering: each card due ≤ next card due
        for j in range(len(due) - 1):
            self.assertLessEqual(due[j].due_datetime, due[j + 1].due_datetime)

    def test_scheduler_updated_after_algorithm_reschedule(self):
        """
        After a review, the card's due_datetime changes.  The Scheduler must
        reflect the new position when update_card is called.
        """
        card = Card(
            card_id="reschedule_card",
            user_id="u1",
            front="Q",
            back="A",
            state=CardState.REVIEW,
            interval_days=1.0,
            ease_factor=2.5,
            due_datetime=datetime.utcnow() - timedelta(days=1),
        )
        self.storage.save_card(card)
        self.sched.add_card(card)

        # It should be due right now
        due_before = self.sched.get_due_cards(reference_time=datetime.utcnow())
        self.assertEqual(len(due_before), 1)

        # Apply a successful review → next due becomes days in the future
        card = self.storage.get_card("reschedule_card")
        card, update = _review_card_with_algo(
            self.storage, self.algo, card, quality=4,
            session_id="rs_sess", review_id="rs_r1"
        )

        # Tell the scheduler about the new schedule
        self.sched.update_card(card)

        # Now it should NOT be in the due list
        due_after = self.sched.get_due_cards(reference_time=datetime.utcnow())
        due_ids = [c.card_id for c in due_after]
        self.assertNotIn("reschedule_card", due_ids)

    def test_multi_user_scheduler_isolation(self):
        """
        Cards for user_A and user_B are both added to the same Scheduler.
        get_due_cards filtered by user returns only that user's cards.
        """
        for uid in ["user_A", "user_B"]:
            self._load_cards_to_scheduler(uid, n=5, days_overdue=-1.0)

        # get_due_cards with user_id filter
        due_a = self.sched.get_due_cards(
            reference_time=datetime.utcnow(), user_id="user_A"
        )
        due_b = self.sched.get_due_cards(
            reference_time=datetime.utcnow(), user_id="user_B"
        )

        self.assertEqual(len(due_a), 5)
        self.assertEqual(len(due_b), 5)

        for c in due_a:
            self.assertEqual(c.user_id, "user_A")
        for c in due_b:
            self.assertEqual(c.user_id, "user_B")


class TestAlgorithmDifficultyFactorIntegration(unittest.TestCase):
    """
    Test that the adaptive Difficulty Factor (§4.1.5-A) integrates correctly
    with the review history stored in InMemoryStorage.

    What to look out for
    --------------------
    - DF calculated from 30-day review history must match the spec formula:
        DF = 1.0 + (retention_rate - 0.9) × 0.5,  clamped to [0.7, 1.3]
    - A user with 100% retention should get a higher DF (harder schedule).
    - A user with 70% retention should get a lower DF (easier schedule).
    - DF must always stay within [0.7, 1.3].
    """

    def setUp(self):
        self.storage = InMemoryStorage()
        self.algo = SM2Plus()

    def _save_reviews_with_success_rate(
        self, user_id: str, total: int, successes: int
    ):
        """Create synthetic review history for testing DF calculation."""
        for i in range(total):
            q = 4 if i < successes else 1  # 4 → success, 1 → failure
            review = Review(
                review_id=f"{user_id}_r{i}",
                card_id=f"card_{i}",
                user_id=user_id,
                session_id="test_session",
                quality=q,
                time_taken_seconds=5.0,
                state_before=CardState.REVIEW,
                interval_before=5.0,
                ease_factor_before=2.5,
                state_after=CardState.REVIEW if q >= 3 else CardState.RELEARNING,
                interval_after=7.5 if q >= 3 else 2.5,
                ease_factor_after=2.5 if q >= 3 else 2.3,
                due_datetime_after=datetime.utcnow() + timedelta(days=7),
            )
            self.storage.save_review(review)

    def test_high_retention_produces_higher_df(self):
        """User with 95% retention gets DF > 1.0."""
        self._save_reviews_with_success_rate("high_ret", total=100, successes=95)
        reviews = self.storage.get_reviews(user_id="high_ret")
        retention = sum(1 for r in reviews if r.quality >= 3) / len(reviews)

        df = self.algo.calculate_difficulty_factor(retention)
        self.assertGreater(df, 1.0)

    def test_low_retention_produces_lower_df(self):
        """User with 75% retention gets DF < 1.0."""
        self._save_reviews_with_success_rate("low_ret", total=100, successes=75)
        reviews = self.storage.get_reviews(user_id="low_ret")
        retention = sum(1 for r in reviews if r.quality >= 3) / len(reviews)

        df = self.algo.calculate_difficulty_factor(retention)
        self.assertLess(df, 1.0)

    def test_df_always_within_bounds(self):
        """DF must remain in [0.7, 1.3] regardless of extreme retention rates."""
        for retention in [0.0, 0.5, 0.9, 0.95, 1.0]:
            df = self.algo.calculate_difficulty_factor(retention)
            self.assertGreaterEqual(df, 0.7, msg=f"retention={retention}")
            self.assertLessEqual(df, 1.3, msg=f"retention={retention}")

    def test_df_applied_in_interval_calculation(self):
        """
        When DF is applied, a high-retention user's next interval should be
        longer than a low-retention user's for the same card/quality.
        """
        card_high = Card(
            card_id="df_high", user_id="u_high", front="Q", back="A",
            state=CardState.REVIEW, interval_days=10.0, ease_factor=2.5,
        )
        card_low = Card(
            card_id="df_low", user_id="u_low", front="Q", back="A",
            state=CardState.REVIEW, interval_days=10.0, ease_factor=2.5,
        )
        self.storage.save_card(card_high)
        self.storage.save_card(card_low)

        update_high = self.algo.calculate_next_interval(
            card_high, quality=4, difficulty_factor=1.2
        )
        update_low = self.algo.calculate_next_interval(
            card_low, quality=4, difficulty_factor=0.8
        )

        self.assertGreater(
            update_high.interval_days, update_low.interval_days,
            msg="High DF should produce a longer interval than low DF",
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
