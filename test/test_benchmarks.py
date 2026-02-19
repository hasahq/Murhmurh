"""
Performance Benchmark Tests — SP-Quiz Phase 2
sp_quiz/tests/test_benchmarks.py
==============================================

Acceptance criteria from §9.2:
    - Algorithm produces mathematically correct intervals                ✓ (test_sm2_plus.py)
    - Edge cases handled (first review, lapses, max intervals)           ✓ (test_sm2_plus.py)
    - **Performance meets targets (< 1 ms per calculation)**             ← THIS FILE
    - **Algorithm is deterministic for same inputs**                     ← THIS FILE

Benchmarks defined here
-----------------------
1. ``TestAlgorithmPerformance``
   • single SM-2+ calculation in < 1 ms                (§9.2 hard target)
   • 10 000 consecutive calculations complete in < 1 s
   • ease_factor adjustment in < 0.1 ms
   • lapse handling in < 0.5 ms
   • difficulty factor calculation in < 0.1 ms

2. ``TestSchedulerPerformance``
   • 1 000 card inserts in < 100 ms
   • get_due_cards on 10 000 card queue in < 50 ms
   • 1 000 successive pop_next_due in < 10 ms

3. ``TestDeterminism``
   • 100 identical runs of calculate_next_interval produce identical results
   • Hashing-based equality check for ScheduleUpdate fields

Notes
-----
These tests are intentionally lenient on CI machines (multipliers applied).
Set the ``BENCHMARK_STRICT`` environment variable to '1' to enforce the spec
targets without any multiplier.

Running the tests
-----------------
::

    python -m pytest test_benchmarks.py -v
    python -m pytest test_benchmarks.py -v -s          # shows timings
    python -m unittest test_benchmarks -v
    BENCHMARK_STRICT=1 python -m pytest test_benchmarks.py   # strict mode

What to look out for
--------------------
- Any single calculation exceeding 1 ms is a regression.
- A non-deterministic result (rare flicker) indicates shared mutable state.
- Scheduler pop performance degrading super-linearly signals a broken heap.
"""

import os
import time
import unittest
from datetime import datetime, timedelta

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.algorithms.sm2_plus import SM2Plus
from sp_quiz.algorithms.scheduler import Scheduler
from sp_quiz.core.card import Card, CardState

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# In strict mode (CI gate) keep to the spec targets.
# In non-strict mode allow 5× slack for slow virtualised environments.
_STRICT = os.environ.get("BENCHMARK_STRICT", "0") == "1"
_MULTIPLIER = 1.0 if _STRICT else 5.0

_MAX_CALC_MS     = 1.0   * _MULTIPLIER   # < 1 ms per SM-2 calculation
_MAX_10K_CALC_S  = 1.0   * _MULTIPLIER   # < 1 s for 10 000 calculations
_MAX_EF_MS       = 0.1   * _MULTIPLIER   # < 0.1 ms for adjust_ease_factor
_MAX_LAPSE_MS    = 0.5   * _MULTIPLIER   # < 0.5 ms for handle_lapse
_MAX_DF_MS       = 0.1   * _MULTIPLIER   # < 0.1 ms for difficulty factor
_MAX_1K_INS_MS   = 100.0 * _MULTIPLIER   # < 100 ms for 1 000 scheduler inserts
_MAX_DUE_50_MS   = 50.0  * _MULTIPLIER   # < 50 ms for get_due_cards on 10k queue
_MAX_1K_POP_MS   = 10.0  * _MULTIPLIER   # < 10 ms for 1 000 pops


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_new_card(card_id: str = "c0") -> Card:
    return Card(
        card_id=card_id, user_id="u1", front="Q", back="A",
        state=CardState.NEW, interval_days=0.0, ease_factor=2.5,
        learning_step=0, reviews_count=0, lapses_count=0,
    )


def _make_review_card(card_id: str = "cr", interval_days: float = 5.0) -> Card:
    return Card(
        card_id=card_id, user_id="u1", front="Q", back="A",
        state=CardState.REVIEW, interval_days=interval_days,
        ease_factor=2.5, learning_step=0, reviews_count=10, lapses_count=0,
    )


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


# ---------------------------------------------------------------------------
# Test: Algorithm Calculation Performance
# ---------------------------------------------------------------------------

class TestAlgorithmPerformance(unittest.TestCase):
    """
    All SM-2+ calculations must meet the < 1 ms per-call target from §9.2.

    Failure here does NOT mean the algorithm logic is wrong — it means an
    optimisation pass is needed before shipping to production.
    """

    def setUp(self):
        self.algo = SM2Plus()

    def test_single_calculation_under_1ms(self):
        """A single calculate_next_interval call must complete in < 1 ms."""
        card = _make_review_card()

        # Warm-up to avoid cold-start JIT effects
        self.algo.calculate_next_interval(_make_review_card("warm"), quality=4)

        start = time.perf_counter()
        self.algo.calculate_next_interval(card, quality=4)
        elapsed = _elapsed_ms(start)

        self.assertLess(
            elapsed, _MAX_CALC_MS,
            msg=f"SM-2 calculation took {elapsed:.3f} ms (limit: {_MAX_CALC_MS} ms)",
        )

    def test_10000_calculations_complete_under_1_second(self):
        """
        10 000 consecutive SM-2 calculations must complete in under 1 second.

        This directly verifies the throughput target of >1 000 reviews/s
        implied by §7.1 (Submit review < 15 ms at 5000 req/s).
        """
        start = time.perf_counter()
        for i in range(10_000):
            card = _make_review_card(card_id=f"c{i}", interval_days=float(i % 30 + 1))
            self.algo.calculate_next_interval(card, quality=(i % 6))
        elapsed = time.perf_counter() - start

        self.assertLess(
            elapsed, _MAX_10K_CALC_S,
            msg=f"10 000 SM-2 calculations took {elapsed:.3f} s (limit: {_MAX_10K_CALC_S} s)",
        )

    def test_ease_factor_adjustment_under_0_1ms(self):
        """adjust_ease_factor must be near-instant."""
        # Warm-up
        self.algo.adjust_ease_factor(2.5, quality=4)

        start = time.perf_counter()
        self.algo.adjust_ease_factor(2.5, quality=4)
        elapsed = _elapsed_ms(start)

        self.assertLess(
            elapsed, _MAX_EF_MS,
            msg=f"adjust_ease_factor took {elapsed:.4f} ms (limit: {_MAX_EF_MS} ms)",
        )

    def test_lapse_handling_under_0_5ms(self):
        """handle_lapse must complete in < 0.5 ms."""
        card = _make_review_card()

        # Warm-up
        self.algo.handle_lapse(_make_review_card("warm"))

        start = time.perf_counter()
        self.algo.handle_lapse(card)
        elapsed = _elapsed_ms(start)

        self.assertLess(
            elapsed, _MAX_LAPSE_MS,
            msg=f"handle_lapse took {elapsed:.4f} ms (limit: {_MAX_LAPSE_MS} ms)",
        )

    def test_difficulty_factor_calculation_under_0_1ms(self):
        """calculate_difficulty_factor must be near-instant."""
        self.algo.calculate_difficulty_factor(0.9)  # warm-up

        start = time.perf_counter()
        self.algo.calculate_difficulty_factor(0.85)
        elapsed = _elapsed_ms(start)

        self.assertLess(
            elapsed, _MAX_DF_MS,
            msg=(
                f"calculate_difficulty_factor took {elapsed:.4f} ms "
                f"(limit: {_MAX_DF_MS} ms)"
            ),
        )

    def test_throughput_all_quality_levels(self):
        """
        Run 1 000 calculations for each of the 6 quality levels.
        All must finish in under 1 s combined.
        """
        start = time.perf_counter()
        for q in range(6):
            for i in range(1_000):
                card = _make_review_card(card_id=f"q{q}_c{i}", interval_days=5.0)
                self.algo.calculate_next_interval(card, quality=q)
        elapsed = time.perf_counter() - start

        self.assertLess(
            elapsed, _MAX_10K_CALC_S,
            msg=f"6×1 000 quality calculations took {elapsed:.3f} s (limit: {_MAX_10K_CALC_S} s)",
        )


# ---------------------------------------------------------------------------
# Test: Scheduler Performance
# ---------------------------------------------------------------------------

class TestSchedulerPerformance(unittest.TestCase):
    """
    Priority-queue operations must satisfy O(log n) complexity requirements.

    §4.2: Insert O(log n), peek O(1), pop O(log n).
    """

    def _make_sched_card(self, i: int, offset_days: float) -> Card:
        return Card(
            card_id=f"sc{i}", user_id="u1", front="Q", back="A",
            state=CardState.REVIEW,
            due_datetime=datetime.utcnow() + timedelta(days=offset_days),
            interval_days=1.0, ease_factor=2.5,
        )

    def test_1000_inserts_under_100ms(self):
        """1 000 add_card operations on a Scheduler must complete in < 100 ms."""
        sched = Scheduler()
        cards = [self._make_sched_card(i, float(i)) for i in range(1_000)]

        start = time.perf_counter()
        for card in cards:
            sched.add_card(card)
        elapsed = _elapsed_ms(start)

        self.assertLess(
            elapsed, _MAX_1K_INS_MS,
            msg=f"1 000 inserts took {elapsed:.2f} ms (limit: {_MAX_1K_INS_MS} ms)",
        )

    def test_get_due_cards_on_10k_queue_under_50ms(self):
        """
        get_due_cards() on a 10 000-card queue must complete in < 50 ms.

        Half the cards are overdue, half are future — realistic workload.
        """
        sched = Scheduler()
        now = datetime.utcnow()
        for i in range(10_000):
            offset = -5.0 if i % 2 == 0 else 5.0  # alternating past/future
            sched.add_card(self._make_sched_card(i, offset))

        start = time.perf_counter()
        due = sched.get_due_cards(reference_time=now)
        elapsed = _elapsed_ms(start)

        self.assertLess(
            elapsed, _MAX_DUE_50_MS,
            msg=f"get_due_cards (10 000 cards) took {elapsed:.2f} ms (limit: {_MAX_DUE_50_MS} ms)",
        )
        # Sanity: should have returned ~5 000 cards
        self.assertGreater(len(due), 4_000)

    def test_1000_successive_pops_under_10ms(self):
        """1 000 pop_next_due operations must complete in < 10 ms."""
        sched = Scheduler()
        for i in range(1_000):
            sched.add_card(self._make_sched_card(i, float(i)))

        start = time.perf_counter()
        while sched.size() > 0:
            sched.pop_next_due()
        elapsed = _elapsed_ms(start)

        self.assertLess(
            elapsed, _MAX_1K_POP_MS,
            msg=f"1 000 pops took {elapsed:.2f} ms (limit: {_MAX_1K_POP_MS} ms)",
        )


# ---------------------------------------------------------------------------
# Test: Determinism
# ---------------------------------------------------------------------------

class TestDeterminism(unittest.TestCase):
    """
    The SM-2+ algorithm must be fully deterministic: identical inputs produce
    identical outputs across 100 independent invocations.

    §9.2 Acceptance Criterion: "Algorithm is deterministic for same inputs."
    """

    def setUp(self):
        self.algo = SM2Plus()

    def _snapshot(self, update) -> tuple:
        """Stable fingerprint for a ScheduleUpdate."""
        return (
            round(update.interval_days, 8),
            round(update.new_ease_factor, 8),
            update.new_state,
            update.new_learning_step,
        )

    def test_determinism_new_card_100_runs(self):
        """100 identical NEW-card reviews produce identical ScheduleUpdate."""
        results = set()
        for _ in range(100):
            card = Card(
                card_id="det_card", user_id="u1", front="Q", back="A",
                state=CardState.NEW, interval_days=0.0, ease_factor=2.5,
                learning_step=0, reviews_count=0, lapses_count=0,
            )
            update = self.algo.calculate_next_interval(card, quality=4)
            results.add(self._snapshot(update))

        self.assertEqual(
            len(results), 1,
            msg=f"Expected 1 unique result, got {len(results)}: {results}",
        )

    def test_determinism_review_card_all_qualities(self):
        """For each quality (0-5), 50 runs must all return the same result."""
        for q in range(6):
            with self.subTest(quality=q):
                results = set()
                for _ in range(50):
                    card = Card(
                        card_id="det_rev", user_id="u1", front="Q", back="A",
                        state=CardState.REVIEW, interval_days=7.0,
                        ease_factor=2.2, learning_step=0,
                        reviews_count=15, lapses_count=1,
                    )
                    update = self.algo.calculate_next_interval(card, quality=q)
                    results.add(self._snapshot(update))

                self.assertEqual(
                    len(results), 1,
                    msg=f"q={q}: Expected 1 unique result, got {len(results)}",
                )

    def test_determinism_lapse_handling(self):
        """handle_lapse produces the same output on 50 identical inputs."""
        results = set()
        for _ in range(50):
            card = Card(
                card_id="det_lapse", user_id="u1", front="Q", back="A",
                state=CardState.REVIEW, interval_days=20.0,
                ease_factor=2.0, learning_step=0,
                reviews_count=20, lapses_count=2,
            )
            update = self.algo.handle_lapse(card)
            results.add(self._snapshot(update))

        self.assertEqual(len(results), 1)


# ---------------------------------------------------------------------------
# Test: Memory Footprint (light sanity only — not a full memory test)
# ---------------------------------------------------------------------------

class TestMemoryFootprint(unittest.TestCase):
    """
    §7.2: Per-user session < 1 MB.  Card cache target < 50 MB for 100 k cards.

    This is a lightweight sanity check — a full memory profile requires
    external tooling (memory_profiler / tracemalloc).
    """

    def test_10k_cards_in_scheduler_feasible(self):
        """
        Creating 10 000 Card objects + loading them into Scheduler must not
        crash or take an unreasonable amount of memory on standard hardware.
        This test verifies functional feasibility, not an exact byte count.
        """
        sched = Scheduler()
        for i in range(10_000):
            card = Card(
                card_id=f"mem_{i}",
                user_id="u1",
                front=f"Question {i}",
                back=f"Answer {i}",
                state=CardState.REVIEW,
                due_datetime=datetime.utcnow() + timedelta(days=float(i % 365)),
                interval_days=float(i % 30 + 1),
                ease_factor=2.5,
            )
            sched.add_card(card)

        self.assertEqual(sched.size(), 10_000)

    @unittest.skipUnless(
        hasattr(__import__("sys"), "getsizeof"),
        "sys.getsizeof not available",
    )
    def test_schedule_update_is_lightweight(self):
        """
        A single ScheduleUpdate object must not consume excessive memory.
        Threshold: < 2 KB per object.
        """
        import sys as _sys
        algo = SM2Plus()
        card = Card(
            card_id="sz_card", user_id="u1", front="Q", back="A",
            state=CardState.REVIEW, interval_days=5.0, ease_factor=2.5,
        )
        update = algo.calculate_next_interval(card, quality=4)
        size = _sys.getsizeof(update)
        self.assertLess(
            size, 2048,
            msg=f"ScheduleUpdate size is {size} bytes (expected < 2048)",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
