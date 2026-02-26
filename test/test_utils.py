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

class TestCalculateInterval(unittest.TestCase):
    """Tests Utilities that Calculate Review Intervals"""

    def test_basic_multiplication(self):
        """new_interval = prev × EF × DF (within clamping range)."""
        result = calculate_interval(
            previous_interval=1.0, ease_factor=2.5, difficulty_factor=1.0
        )
        self.assertAlmostEqual(result, 2.5, places=5)

    def test_ef_df_both_one_is_identity(self):
        """EF=1.0, DF=1.0 → output equals previous_interval."""
        for prev in [1.0, 5.0, 30.0, 100.0]:
            result = calculate_interval(
                previous_interval=prev, ease_factor=1.0, difficulty_factor=1.0
            )
            self.assertAlmostEqual(result, prev, places=5)

    def test_minimum_interval_enforced(self):
        """Result must be ≥ MIN_INTERVAL_DAYS."""
        result = calculate_interval(
            previous_interval=0.000001, ease_factor=0.01, difficulty_factor=0.01
        )
        self.assertGreaterEqual(result, MIN_INTERVAL_DAYS)

    def test_maximum_interval_enforced(self):
        """Result must be ≤ MAX_INTERVAL_DAYS (365 days)."""
        result = calculate_interval(
            previous_interval=300.0, ease_factor=2.5, difficulty_factor=1.3
        )
        self.assertLessEqual(result, MAX_INTERVAL_DAYS)

    def test_difficulty_factor_scales_interval(self):
        """Higher DF → longer interval."""
        low = calculate_interval(1.0, 2.5, difficulty_factor=0.7)
        high = calculate_interval(1.0, 2.5, difficulty_factor=1.3)
        self.assertLess(low, high)




class TestDaysTimedeltaConversion(unittest.TestCase):
    """Test: days_to_timedelta / timedelta_to_days"""

    def test_days_to_timedelta_integer(self):
        td = days_to_timedelta(1.0)
        self.assertEqual(td, timedelta(days=1))

    def test_days_to_timedelta_fractional(self):
        """0.5 days = 12 hours."""
        td = days_to_timedelta(0.5)
        self.assertAlmostEqual(td.total_seconds(), 12 * 3600, delta=1)

    def test_timedelta_to_days_one_day(self):
        days = timedelta_to_days(timedelta(days=1))
        self.assertAlmostEqual(days, 1.0, places=8)

    def test_timedelta_to_days_fractional(self):
        td = timedelta(hours=6)  # 0.25 days
        days = timedelta_to_days(td)
        self.assertAlmostEqual(days, 0.25, places=8)

    def test_round_trip_days_to_timedelta_and_back(self):
        for d in [0.0, 0.5, 1.0, 7.5, 30.0]:
            td = days_to_timedelta(d)
            recovered = timedelta_to_days(td)
            self.assertAlmostEqual(recovered, d, places=7, msg=f"days={d}")

    def test_returns_correct_types(self):
        self.assertIsInstance(days_to_timedelta(1.0), timedelta)
        self.assertIsInstance(timedelta_to_days(timedelta(days=1)), float)



class TestRetentionFromInterval(unittest.TestCase):
    """Tests retention_from_interval(interval_days, stability)"""

    def test_return_value_in_unit_interval(self):
        for interval in [0, 1, 7, 30, 365]:
            r = retention_from_interval(float(interval), stability=10.0)
            self.assertGreaterEqual(r, 0.0)
            self.assertLessEqual(r, 1.0)

    def test_matches_forgetting_curve(self):
        """retention_from_interval is an alias for forgetting_curve."""
        stability = 8.0
        for t in [0.0, 1.0, 5.0, 20.0]:
            self.assertAlmostEqual(
                retention_from_interval(t, stability),
                forgetting_curve(t, stability),
                places=8,
            )

    def test_returns_float(self):
        r = retention_from_interval(1.0, stability=5.0)
        self.assertIsInstance(r, float)


class TestStabilityFromReviews(unittest.TestCase):
    """Tests Stability from Reviews in 
    relation to their average quality and count
    stability_from_reviews(reviews_count, average_quality)"""

    def test_positive_stability(self):
        """Stability must always be strictly positive."""
        for n, q in [(1, 3.0), (5, 4.0), (20, 4.5), (100, 5.0)]:
            s = stability_from_reviews(n, q)
            self.assertGreater(s, 0, msg=f"n={n}, q={q}")

    def test_stability_increases_with_review_count(self):
        """More reviews (with same quality) → higher stability."""
        q = 4.0
        stabilities = [stability_from_reviews(n, q) for n in [1, 5, 20, 100]]
        for i in range(len(stabilities) - 1):
            self.assertLessEqual(stabilities[i], stabilities[i + 1])

    def test_stability_increases_with_average_quality(self):
        """Higher average quality → higher stability (fixed count)."""
        n = 10
        s_low = stability_from_reviews(n, average_quality=2.0)
        s_high = stability_from_reviews(n, average_quality=5.0)
        self.assertLess(s_low, s_high)

    def test_returns_float(self):
        self.assertIsInstance(stability_from_reviews(5, 4.0), float)

    def test_zero_reviews_handled(self):
        """Zero reviews should not crash — may return a baseline stability."""
        try:
            s = stability_from_reviews(0, average_quality=0.0)
            self.assertGreaterEqual(s, 0)
        except (ValueError, ZeroDivisionError):
            pass  # also acceptable if implementation raises


if __name__ == "__main__":
    unittest.main(verbosity=2)