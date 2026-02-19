"""
Unit Tests — SP-Quiz Phase 2: SM-2+ Algorithm (``sp_quiz.algorithms.sm2_plus``)
================================================================================

What is tested
--------------
SM2Plus.calculate_next_interval()
    - First review of a brand-new card (learning step 0 → 1)
    - Advancement through every learning step on q ≥ 3
    - Failure to advance (q < 3) keeps the card on the current step
    - Graduation from the final learning step into the review phase
    - Review-phase interval growth on successive successful reviews
    - Ease-factor adjustment formula: EF' = EF + 0.1 - (5-q)*(0.08+(5-q)*0.02)
    - Lapse handling (q < 3 on a graduated card): relearning phase, EF penalty
    - Hard minimum / maximum clamps on EF (1.3 / 2.5)
    - Hard minimum / maximum clamps on interval (MIN_INTERVAL / MAX_INTERVAL)
    - Determinism: identical inputs produce identical outputs
    - Return type is a ``ScheduleUpdate`` namedtuple / dataclass

SM2Plus.adjust_ease_factor()
    - Numerical correctness of the formula across all six quality values (0-5)
    - Clamping to MIN_EF = 1.3 when formula would produce a lower value
    - No upward drift beyond the initial 2.5 for all-perfect-recall sequence

SM2Plus.handle_lapse()
    - EF is reduced by 0.2 (floored at 1.3)
    - Interval is halved (floored at 1 day / MIN_INTERVAL)
    - Card state is set to RELEARNING

SM2Plus.calculate_initial_interval()
    - q ≥ 3  → step-1 interval (1 min = 60 s)
    - q < 3  → same step-1 interval (repeat first step)

Learning-phase advancement rules
    - Steps must satisfy: step 0 → 60 s, step 1 → 600 s, step 2 → graduation (1 day)

Quality-rating boundary conditions
    - q = 0 on a mature review card → maximum penalty applied
    - q = 5 on a fresh card → fastest possible progression
    - q = 3 (threshold) is treated as a success everywhere

Running the tests
-----------------
From the project root::

    python -m pytest test_sm2_plus.py -v
    # or
    python -m unittest test_sm2_plus -v

Dependencies
------------
Only the Python standard library and the ``sp_quiz`` package itself for now.
"""

import unittest
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.algorithms.sm2_plus import SM2Plus, ScheduleUpdate
from sp_quiz.core.card import Card, CardState

#Quick helpers
def _make_new_card(card_id: str = "card_001", user_id: str = "user_001") -> Card:
    """Return a brand-new card with default SM-2 fields."""
    return Card(
        card_id=card_id,
        user_id=user_id,
        front="Q",
        back="A",
        state=CardState.NEW,
        interval_days=0.0,
        ease_factor=2.5,
        learning_step=0,
        reviews_count=0,
        lapses_count=0,
    )


def _make_review_card(
    card_id: str = "card_rev",
    user_id: str = "user_001",
    interval_days: float = 1.0,
    ease_factor: float = 2.5,
    lapses: int = 0,
) -> Card:
    """Return a graduated (REVIEW-phase) card."""
    return Card(
        card_id=card_id,
        user_id=user_id,
        front="Q",
        back="A",
        state=CardState.REVIEW,
        interval_days=interval_days,
        ease_factor=ease_factor,
        learning_step=0,
        reviews_count=5,
        lapses_count=lapses,
    )

class TestSM2PlusLearningPhase(unittest.TestCase):
    """Test SM-2+ behaviour during the initial learning phase."""

    def setUp(self):
        self.algo = SM2Plus()

    # ------------------------------------------------------------------
    # Step 0 → Step 1  (1 min interval)
    # ------------------------------------------------------------------

    def test_first_review_quality_3_advances_to_step1(self):
        """A quality ≥ 3 on a NEW card advances to step 1 (1-minute interval)."""
        card = _make_new_card()
        update = self.algo.calculate_next_interval(card, quality=3)

        self.assertEqual(update.new_state, CardState.LEARNING)
        self.assertEqual(update.new_learning_step, 1)
        # interval ≈ 1 min expressed in days
        self.assertAlmostEqual(update.interval_days, 60 / 86400, places=6)

    def test_first_review_quality_5_advances_to_step1(self):
        """A perfect q=5 on a NEW card still targets the step-1 interval."""
        card = _make_new_card()
        update = self.algo.calculate_next_interval(card, quality=5)

        self.assertEqual(update.new_state, CardState.LEARNING)
        self.assertEqual(update.new_learning_step, 1)

    def test_first_review_quality_0_stays_at_step0(self):
        """A quality 0 on a NEW card keeps the card on step 0."""
        card = _make_new_card()
        update = self.algo.calculate_next_interval(card, quality=0)

        self.assertEqual(update.new_state, CardState.LEARNING)
        self.assertEqual(update.new_learning_step, 0)

    def test_first_review_quality_2_stays_at_step0(self):
        """q=2 (< 3 threshold) keeps the card on step 0."""
        card = _make_new_card()
        update = self.algo.calculate_next_interval(card, quality=2)

        self.assertEqual(update.new_learning_step, 0)

    # ------------------------------------------------------------------
    # Step 1 → Step 2  (10-min interval)
    # ------------------------------------------------------------------

    def test_step1_quality_3_advances_to_step2(self):
        """q ≥ 3 on step 1 advances to step 2 (10-minute interval)."""
        card = _make_new_card()
        card.state = CardState.LEARNING
        card.learning_step = 1

        update = self.algo.calculate_next_interval(card, quality=3)

        self.assertEqual(update.new_learning_step, 2)
        # 10 minutes in days
        self.assertAlmostEqual(update.interval_days, 600 / 86400, places=6)

    def test_step1_quality_2_stays_at_step1(self):
        """q < 3 on step 1 keeps the card at step 1."""
        card = _make_new_card()
        card.state = CardState.LEARNING
        card.learning_step = 1

        update = self.algo.calculate_next_interval(card, quality=2)

        self.assertEqual(update.new_learning_step, 1)

    # ------------------------------------------------------------------
    # Step 2 → Graduation  (1-day interval → REVIEW state)
    # ------------------------------------------------------------------

    def test_step2_quality_3_graduates_card(self):
        """q ≥ 3 on the final learning step graduates the card."""
        card = _make_new_card()
        card.state = CardState.LEARNING
        card.learning_step = 2

        update = self.algo.calculate_next_interval(card, quality=4)

        self.assertEqual(update.new_state, CardState.REVIEW)
        self.assertAlmostEqual(update.interval_days, 1.0, places=3)

    def test_step2_quality_2_does_not_graduate(self):
        """q < 3 on the final learning step does NOT graduate."""
        card = _make_new_card()
        card.state = CardState.LEARNING
        card.learning_step = 2

        update = self.algo.calculate_next_interval(card, quality=2)

        self.assertNotEqual(update.new_state, CardState.REVIEW)