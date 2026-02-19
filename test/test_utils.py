"""
Unit Tests — SP-Quiz Mathematical Utilities (Phase 2) (``sp_quiz.algorithms.utils``)
====================================================================================

What is tested
--------------
forgetting_curve(t, stability)
    - R(0) == 1.0  (full recall immediately after learning)
    - R(t) decreases monotonically as t increases (Ebbinghaus decay)
    - R(t) → 0 as t → ∞ (asymptotic behaviour)
    - With t == stability, R ≈ 1/e ≈ 0.368
    - Raises / handles t < 0 gracefully

clamp(value, min_val, max_val)
    - value in range → returned unchanged
    - value < min_val → returns min_val
    - value > max_val → returns max_val
    - min_val == max_val → always returns that value

ease_factor_delta(quality)
    - Matches the formula: 0.1 - (5-q)*(0.08 + (5-q)*0.02)  for q ∈ {0..5}
    - q=4 produces delta ≈ 0.0 (neutral)
    - q=5 produces delta > 0 (improvement)
    - q=3 produces a small negative delta

calculate_interval(previous_interval, ease_factor, difficulty_factor)
    - Output = max(MIN_INTERVAL, previous * EF * DF)
    - Output ≤ MAX_INTERVAL (clamping)
    - With EF=1.0 and DF=1.0 output equals previous_interval (identity)

days_to_timedelta / timedelta_to_days
    - Round-trip: to_timedelta(to_days(td)) == td  (within floating-point tolerance)
    - Handles fractional days correctly (hours, minutes, seconds)
    - Returns timedelta / float types respectively

retention_from_interval(interval_days, stability)
    - Matches forgetting_curve(interval_days, stability)
    - Returns float in [0.0, 1.0]

stability_from_reviews(reviews_count, average_quality)
    - Stability increases with more reviews (monotonic with count)
    - Stability increases with average quality
    - Returns a positive float

Running the tests
-----------------
::

    python -m pytest test_utils.py -v
    python -m unittest test_utils -v
"""

import math
import unittest
from datetime import timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.algorithms.utils import (
    forgetting_curve,
    clamp,
    ease_factor_delta,
    calculate_interval,
    days_to_timedelta,
    timedelta_to_days,
    retention_from_interval,
    stability_from_reviews
)

# Design Specification Defined constants
MIN_INTERVAL_DAYS = 60 / 86400   # 1 min in fractional days
MAX_INTERVAL_DAYS = 365.0        # 365 days


class TestForgettingCurve(unittest.TestCase):
    """Tests Forgetting Curve and its Stability `forgetting_curve(t, stability)`"""
    
    def test_recall_at_t_zero_is_one(self):
        """Immediately after learning recall probability == 1.0."""
        r = forgetting_curve(t=0.0, stability=5.0)
        self.assertAlmostEqual(r, 1.0, places=8)

    def test_monotonically_decreasing(self):
        """R(t) must decrease as t increases (holding stability fixed)."""
        stability = 10.0
        prev_r = forgetting_curve(t=0.0, stability=stability)
        for t in [1.0, 3.0, 7.0, 14.0, 30.0, 100.0]:
            r = forgetting_curve(t=t, stability=stability)
            self.assertLess(r, prev_r, msg=f"R did not decrease at t={t}")
            prev_r = r

    def test_r_approaches_zero_asymptotically(self):
        """For very large t, R(t) should be close to zero."""
        r = forgetting_curve(t=10_000.0, stability=1.0)
        self.assertAlmostEqual(r, 0.0, places=5)

    def test_r_at_t_equals_stability_is_inverse_e(self):
        """R(S) = e^(-1) ≈ 0.36788."""
        for s in [1.0, 5.0, 30.0]:
            r = forgetting_curve(t=s, stability=s)
            self.assertAlmostEqual(r, math.exp(-1), places=5, msg=f"stability={s}")

    def test_r_always_in_unit_interval(self):
        """R must always lie in [0, 1]."""
        for t in [0, 0.5, 1, 7, 30, 365]:
            r = forgetting_curve(t=float(t), stability=10.0)
            self.assertGreaterEqual(r, 0.0)
            self.assertLessEqual(r, 1.0)

    def test_higher_stability_slower_forgetting(self):
        """Greater stability → higher recall at the same t."""
        t = 5.0
        r_low = forgetting_curve(t=t, stability=3.0)
        r_high = forgetting_curve(t=t, stability=20.0)
        self.assertGreater(r_high, r_low)

    def test_negative_t_handled(self):
        """Negative time should not crash and can return 1.0 or raise ValueError."""
        try:
            r = forgetting_curve(t=-1.0, stability=5.0)
            # If it doesn't raise, result should be ≤ 1.0 and ≥ 0.0
            self.assertLessEqual(r, 1.0)
        except (ValueError, ArithmeticError):
            pass  # also acceptable


class TestClamp(unittest.TestCase):
    """Tests Max and Min clamp values
    clamp(value, min_val, max_val"""

    def test_in_range_unchanged(self):
        self.assertEqual(clamp(2.0, 1.0, 3.0), 2.0)

    def test_below_min_returns_min(self):
        self.assertEqual(clamp(0.5, 1.3, 2.5), 1.3)

    def test_above_max_returns_max(self):
        self.assertEqual(clamp(99.0, 1.3, 2.5), 2.5)

    def test_exactly_at_min(self):
        self.assertEqual(clamp(1.3, 1.3, 2.5), 1.3)

    def test_exactly_at_max(self):
        self.assertEqual(clamp(2.5, 1.3, 2.5), 2.5)

    def test_min_equals_max(self):
        self.assertEqual(clamp(1.0, 2.0, 2.0), 2.0)
        self.assertEqual(clamp(3.0, 2.0, 2.0), 2.0)

    def test_negative_range(self):
        self.assertEqual(clamp(-5.0, -10.0, -1.0), -5.0)
        self.assertEqual(clamp(-15.0, -10.0, -1.0), -10.0)

    def test_integer_inputs(self):
        self.assertEqual(clamp(7, 1, 5), 5)
        self.assertEqual(clamp(0, 1, 5), 1)


class TestEaseFactorDelta(unittest.TestCase):
    """Tests Rate of Change of ease Factor in Quality Reviews
    Δ = 0.1 - (5-q)*(0.08 + (5-q)*0.02)"""

    def _expected_delta(self, q: int) -> float:
        return 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)

    def test_all_quality_values(self):
        for q in range(6):
            with self.subTest(quality=q):
                delta = ease_factor_delta(q)
                self.assertAlmostEqual(delta, self._expected_delta(q), places=8)

    def test_q5_positive_delta(self):
        """q=5 → positive delta (EF increases)."""
        self.assertGreater(ease_factor_delta(5), 0)

    def test_q4_neutral_delta(self):
        """q=4 → delta ≈ 0.0 (EF unchanged)."""
        self.assertAlmostEqual(ease_factor_delta(4), 0.0, places=8)

    def test_q3_slightly_negative_delta(self):
        """q=3 → negative delta."""
        self.assertLess(ease_factor_delta(3), 0)

    def test_q0_largest_negative_delta(self):
        """q=0 has the most negative delta."""
        delta_0 = ease_factor_delta(0)
        delta_1 = ease_factor_delta(1)
        self.assertLess(delta_0, delta_1)

    def test_monotonic_increase_with_quality(self):
        """Higher quality → larger (less negative) delta."""
        deltas = [ease_factor_delta(q) for q in range(6)]
        for i in range(len(deltas) - 1):
            self.assertLess(deltas[i], deltas[i + 1])