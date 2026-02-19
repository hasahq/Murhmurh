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


class TestSM2PlusEaseFactor(unittest.TestCase):
    """Validate the EF adjustment formula for every quality value."""

    # EF' = EF + 0.1 - (5-q)*(0.08 + (5-q)*0.02)

    def setUp(self):
        self.algo = SM2Plus()
        self.initial_ef = 2.5

    def _expected_ef(self, current_ef: float, q: int) -> float:
        raw = current_ef + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        return max(1.3, min(2.5, raw))

    def test_ef_adjustment_q5(self):
        new_ef = self.algo.adjust_ease_factor(self.initial_ef, quality=5)
        self.assertAlmostEqual(new_ef, self._expected_ef(self.initial_ef, 5), places=5)

    def test_ef_adjustment_q4(self):
        new_ef = self.algo.adjust_ease_factor(self.initial_ef, quality=4)
        self.assertAlmostEqual(new_ef, self._expected_ef(self.initial_ef, 4), places=5)

    def test_ef_adjustment_q3(self):
        new_ef = self.algo.adjust_ease_factor(self.initial_ef, quality=3)
        self.assertAlmostEqual(new_ef, self._expected_ef(self.initial_ef, 3), places=5)

    def test_ef_adjustment_q2(self):
        """q=2 should decrease EF."""
        new_ef = self.algo.adjust_ease_factor(self.initial_ef, quality=2)
        self.assertAlmostEqual(new_ef, self._expected_ef(self.initial_ef, 2), places=5)
        self.assertLess(new_ef, self.initial_ef)

    def test_ef_adjustment_q1(self):
        new_ef = self.algo.adjust_ease_factor(self.initial_ef, quality=1)
        self.assertAlmostEqual(new_ef, self._expected_ef(self.initial_ef, 1), places=5)
        self.assertLess(new_ef, self.initial_ef)

    def test_ef_adjustment_q0(self):
        new_ef = self.algo.adjust_ease_factor(self.initial_ef, quality=0)
        self.assertAlmostEqual(new_ef, self._expected_ef(self.initial_ef, 0), places=5)

    def test_ef_clamped_at_min_1_3(self):
        """EF must never fall below 1.3, regardless of repeated low quality."""
        ef = 1.3
        for _ in range(10):
            ef = self.algo.adjust_ease_factor(ef, quality=0)
        self.assertGreaterEqual(ef, 1.3)

    def test_ef_does_not_exceed_initial_with_q5(self):
        """
        Repeated q=5 reviews on a fresh card should not push EF above 2.5.

        Note: The formula for q=5 gives +0.1 which would exceed 2.5 from 2.5,
        so it should be clamped.  (Some implementations start EF below 2.5
        and cap it there — either way it must stay ≤ 2.5.)
        """
        ef = 2.5
        for _ in range(20):
            ef = self.algo.adjust_ease_factor(ef, quality=5)
        self.assertLessEqual(ef, 2.5)

    def test_ef_q4_no_change_from_formula(self):
        """
        q=4 is the 'neutral' quality: EF' = EF + 0.1 - 1*(0.08+1*0.02) = EF + 0.0.
        The formula produces exactly 0 delta, EF unchanged.
        """
        new_ef = self.algo.adjust_ease_factor(2.5, quality=4)
        # delta = 0.1 - 1*(0.08 + 0.02) = 0.1 - 0.10 = 0.0
        self.assertAlmostEqual(new_ef, 2.5, places=5)


class TestSM2PlusIntervalCalculations(unittest.TestCase):
    """Validate interval progression in the review phase."""

    def setUp(self):
        self.algo = SM2Plus()

    def test_first_review_phase_interval_grows(self):
        """Each successful review should extend the interval."""
        card = _make_review_card(interval_days=1.0, ease_factor=2.5)

        update = self.algo.calculate_next_interval(card, quality=4)

        # New interval = 1.0 × 2.5 = 2.5 days
        self.assertGreater(update.interval_days, card.interval_days)
        self.assertAlmostEqual(update.interval_days, 2.5, places=1)

    def test_successive_reviews_compound_interval(self):
        """Simulate 3 consecutive successful reviews and verify compounding."""
        card = _make_review_card(interval_days=1.0, ease_factor=2.5)
        expected = 1.0

        for _ in range(3):
            update = self.algo.calculate_next_interval(card, quality=4)
            card.interval_days = update.interval_days
            card.ease_factor = update.new_ease_factor
            expected *= 2.5  # EF unchanged for q=4

        self.assertAlmostEqual(card.interval_days, expected, places=1)

    def test_interval_minimum_enforced(self):
        """Interval must always be ≥ MIN_INTERVAL (spec: 1 min = 60 s)."""
        card = _make_review_card(interval_days=0.00001)
        update = self.algo.calculate_next_interval(card, quality=0)

        self.assertGreaterEqual(update.interval_days, 60 / 86400)

    def test_interval_maximum_enforced(self):
        """Interval must never exceed MAX_INTERVAL (spec: 365 days)."""
        card = _make_review_card(interval_days=400.0, ease_factor=2.5)
        update = self.algo.calculate_next_interval(card, quality=5)

        self.assertLessEqual(update.interval_days, 365.0)

    def test_interval_does_not_grow_on_lapse(self):
        """A lapse (q < 3) on a review card must not grow the interval."""
        card = _make_review_card(interval_days=30.0, ease_factor=2.5)
        update = self.algo.calculate_next_interval(card, quality=1)

        self.assertLess(update.interval_days, 30.0)

    def test_q3_threshold_succeeds(self):
        """q=3 is the minimum passing quality — interval should grow."""
        card = _make_review_card(interval_days=2.0, ease_factor=2.0)
        update = self.algo.calculate_next_interval(card, quality=3)

        self.assertGreater(update.interval_days, 2.0)


class TestSM2PlusLapseHandling(unittest.TestCase):
    """Test relearning phase triggered by a failed review on a graduated card."""

    def setUp(self):
        self.algo = SM2Plus()

    def test_lapse_sets_relearning_state(self):
        """A q < 3 on a REVIEW card moves it to RELEARNING."""
        card = _make_review_card(interval_days=10.0)
        update = self.algo.handle_lapse(card)

        self.assertEqual(update.new_state, CardState.RELEARNING)

    def test_lapse_halves_interval(self):
        """Interval after a lapse = max(1 day, previous × 0.5)."""
        card = _make_review_card(interval_days=20.0)
        update = self.algo.handle_lapse(card)

        self.assertAlmostEqual(update.interval_days, 10.0, places=3)

    def test_lapse_interval_floored_at_one_day(self):
        """Lapse on a card with 1-day interval does not go below 1 day."""
        card = _make_review_card(interval_days=1.0)
        update = self.algo.handle_lapse(card)

        self.assertGreaterEqual(update.interval_days, 1.0)

    def test_lapse_penalises_ease_factor(self):
        """Ease factor decreases by 0.2 on lapse (floored at 1.3)."""
        card = _make_review_card(interval_days=5.0, ease_factor=2.5)
        update = self.algo.handle_lapse(card)

        expected_ef = max(1.3, 2.5 - 0.2)
        self.assertAlmostEqual(update.new_ease_factor, expected_ef, places=5)

    def test_repeated_lapses_ef_never_below_1_3(self):
        """Multiple lapses must never push EF below 1.3."""
        card = _make_review_card(ease_factor=1.3, lapses=3)
        for _ in range(5):
            update = self.algo.handle_lapse(card)
            card.ease_factor = update.new_ease_factor

        self.assertGreaterEqual(card.ease_factor, 1.3)

    def test_lapse_increments_lapses_count(self):
        """lapses_count on the update must be one more than before."""
        card = _make_review_card(interval_days=5.0, lapses=2)
        update = self.algo.handle_lapse(card)

        self.assertEqual(update.new_lapses_count, 3)

    def test_calculate_next_interval_routes_to_lapse(self):
        """calculate_next_interval with q<3 on REVIEW card == handle_lapse."""
        card_a = _make_review_card(interval_days=10.0, ease_factor=2.5)
        card_b = _make_review_card(interval_days=10.0, ease_factor=2.5)

        via_api = self.algo.calculate_next_interval(card_a, quality=0)
        via_lapse = self.algo.handle_lapse(card_b)

        self.assertEqual(via_api.new_state, via_lapse.new_state)
        self.assertAlmostEqual(via_api.interval_days, via_lapse.interval_days, places=5)
        self.assertAlmostEqual(
            via_api.new_ease_factor, via_lapse.new_ease_factor, places=5
        )


# ---------------------------------------------------------------------------
# Test: calculate_initial_interval()
# ---------------------------------------------------------------------------

class TestSM2PlusInitialInterval(unittest.TestCase):
    """Test the helper that computes the very first interval for a card."""

    def setUp(self):
        self.algo = SM2Plus()

    def test_quality_3_returns_step1_interval(self):
        """q ≥ 3 → first step interval (1 min)."""
        interval = self.algo.calculate_initial_interval(quality=3)
        self.assertAlmostEqual(interval.total_seconds(), 60, delta=1)

    def test_quality_0_returns_step0_interval(self):
        """q < 3 → repeat step 0 (1 min again)."""
        interval = self.algo.calculate_initial_interval(quality=0)
        self.assertIsInstance(interval, timedelta)
        # Any non-negative interval is acceptable for the first step repeat
        self.assertGreaterEqual(interval.total_seconds(), 0)

    def test_return_type_is_timedelta(self):
        interval = self.algo.calculate_initial_interval(quality=5)
        self.assertIsInstance(interval, timedelta)


# ---------------------------------------------------------------------------
# Test: Return Type Contract (ScheduleUpdate)
# ---------------------------------------------------------------------------

class TestScheduleUpdateContract(unittest.TestCase):
    """Ensure calculate_next_interval always returns a well-formed ScheduleUpdate."""

    def setUp(self):
        self.algo = SM2Plus()

    def _assert_valid_update(self, update: ScheduleUpdate):
        self.assertIsNotNone(update)
        self.assertIsInstance(update.interval_days, float)
        self.assertIsInstance(update.new_ease_factor, float)
        self.assertIsInstance(update.new_state, CardState)
        self.assertIsInstance(update.next_due, datetime)
        self.assertGreaterEqual(update.interval_days, 0)
        self.assertGreaterEqual(update.new_ease_factor, 1.3)
        self.assertLessEqual(update.new_ease_factor, 2.5)

    def test_new_card_q5_returns_valid_update(self):
        self._assert_valid_update(
            self.algo.calculate_next_interval(_make_new_card(), quality=5)
        )

    def test_review_card_q4_returns_valid_update(self):
        self._assert_valid_update(
            self.algo.calculate_next_interval(
                _make_review_card(interval_days=2.0), quality=4
            )
        )

    def test_review_card_q0_returns_valid_update(self):
        self._assert_valid_update(
            self.algo.calculate_next_interval(
                _make_review_card(interval_days=2.0), quality=0
            )
        )


# ---------------------------------------------------------------------------
# Test: Determinism
# ---------------------------------------------------------------------------

class TestSM2PlusDeterminism(unittest.TestCase):
    """Same inputs must always yield the same outputs (no hidden randomness)."""

    def setUp(self):
        self.algo = SM2Plus()

    def test_determinism_new_card(self):
        card_a = _make_new_card()
        card_b = _make_new_card()

        update_a = self.algo.calculate_next_interval(card_a, quality=4)
        update_b = self.algo.calculate_next_interval(card_b, quality=4)

        self.assertEqual(update_a.new_state, update_b.new_state)
        self.assertAlmostEqual(update_a.interval_days, update_b.interval_days, places=8)
        self.assertAlmostEqual(
            update_a.new_ease_factor, update_b.new_ease_factor, places=8
        )

    def test_determinism_review_card(self):
        for q in range(6):
            with self.subTest(quality=q):
                card_a = _make_review_card(interval_days=5.0, ease_factor=2.2)
                card_b = _make_review_card(interval_days=5.0, ease_factor=2.2)

                u_a = self.algo.calculate_next_interval(card_a, quality=q)
                u_b = self.algo.calculate_next_interval(card_b, quality=q)

                self.assertEqual(u_a.new_state, u_b.new_state)
                self.assertAlmostEqual(u_a.interval_days, u_b.interval_days, places=8)


class TestSM2PlusBoundaryConditions(unittest.TestCase):
    """Stress the algorithm with extreme or degenerate inputs."""

    def setUp(self):
        self.algo = SM2Plus()

    def test_q0_on_mature_card_maximum_penalty(self):
        """q=0 on a card reviewed 50+ times should apply maximum EF penalty."""
        card = _make_review_card(interval_days=60.0, ease_factor=2.5)
        card.reviews_count = 50
        update = self.algo.calculate_next_interval(card, quality=0)

        # EF must decrease and interval must shrink
        self.assertLess(update.new_ease_factor, 2.5)
        self.assertLess(update.interval_days, 60.0)

    def test_q5_on_fresh_card_fastest_progression(self):
        """q=5 on a brand-new card should reach LEARNING state."""
        card = _make_new_card()
        update = self.algo.calculate_next_interval(card, quality=5)

        self.assertIn(update.new_state, {CardState.LEARNING, CardState.REVIEW})

    def test_very_large_interval_clamped(self):
        """A card with an astronomically large interval is clamped to 365 days."""
        card = _make_review_card(interval_days=1_000.0, ease_factor=2.5)
        update = self.algo.calculate_next_interval(card, quality=5)

        self.assertLessEqual(update.interval_days, 365.0)

    def test_quality_3_is_not_treated_as_lapse(self):
        """q=3 is the minimum success — card must not enter RELEARNING."""
        card = _make_review_card(interval_days=5.0)
        update = self.algo.calculate_next_interval(card, quality=3)

        self.assertNotEqual(update.new_state, CardState.RELEARNING)

    def test_next_due_is_in_the_future(self):
        """next_due datetime must be after the time of calculation."""
        before = datetime.utcnow()
        card = _make_review_card(interval_days=2.0)
        update = self.algo.calculate_next_interval(card, quality=4)

        self.assertGreater(update.next_due, before)

    def test_algorithm_with_zero_interval_card(self):
        """A REVIEW card that somehow has 0-day interval should not crash."""
        card = _make_review_card(interval_days=0.0)
        try:
            update = self.algo.calculate_next_interval(card, quality=4)
            self.assertIsNotNone(update)
        except Exception as exc:  # noqa: BLE001
            self.fail(f"Algorithm raised an exception on zero-interval card: {exc}")