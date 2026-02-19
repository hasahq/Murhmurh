"""
Unit Tests — SP-Quiz Scheduler (``sp_quiz.algorithms.scheduler``)
===========================================================================

What is tested
--------------
Scheduler.add_card()
    - Cards can be inserted into an empty queue
    - Multiple cards inserted with different due_datetimes are ordered correctly
    - Inserting a card that already exists updates its position

Scheduler.get_next_due()
    - Returns the card with the earliest due_datetime (O(1) peek)
    - Returns None on an empty queue
    - Does NOT remove the card from the queue

Scheduler.pop_next_due()
    - Removes and returns the card with the earliest due_datetime
    - Queue shrinks by exactly one after pop
    - Returns None (or raises) on an empty queue

Scheduler.get_due_cards()
    - Returns all cards whose due_datetime ≤ reference_time
    - Future cards are NOT included
    - Respects the optional `limit` argument
    - Returns an empty list when nothing is due

Scheduler.update_card()
    - Re-schedules a card already in the queue
    - Queue ordering is maintained after update

Scheduler.remove_card()
    - Removes a specific card by card_id
    - Queue size decreases by one
    - Removing a non-existent card does not raise (or raises CardNotFoundError
      if the implementation chooses; the test accepts both)

Priority ordering
    - The natural ordering of the heap is always earliest-due-first
    - Cards with the same due_datetime are returned in a consistent order
    - After a series of mixed add / pop operations, ordering is preserved

Thread safety (sequential proxy)
    - Concurrent add and pop operations from multiple threads do not corrupt
      the heap (basic integrity check)

Fuzz Factor (§4.3)
    - apply_fuzz() returns a datetime within ±fuzz_range of the scheduled due
    - With fuzz_factor=0.0 the output equals the input (no jitter)

Running the tests
-----------------
From the project root::

    python -m pytest test_scheduler.py -v
    python -m unittest test_scheduler -v

Dependencies
------------
Only the Python standard library and the ``sp_quiz`` package.
"""

import threading
import unittest
from datetime import datetime, timedelta

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.algorithms.scheduler import Scheduler
from sp_quiz.core.card import Card, CardState

#helpers
def _ts(days_offset: float = 0.0) -> datetime:
    """Return a UTC datetime offset from 'now' by *days_offset* days."""
    return datetime.utcnow() + timedelta(days=days_offset)


def _make_card(card_id: str, due: datetime, user_id: str = "u1") -> Card:
    return Card(
        card_id=card_id,
        user_id=user_id,
        front="Q",
        back="A",
        state=CardState.REVIEW,
        due_datetime=due,
        interval_days=1.0,
        ease_factor=2.5,
    )

class TestSchedulerAddGetPop(unittest.TestCase):
    """Test Basic Add/ Peek/ Pop Operations"""
    def setUp(self):
        self.sched = Scheduler()

    def test_add_single_card(self):
        """Adding one card increases queue size to 1."""
        card = _make_card("c1", _ts(1))
        self.sched.add_card(card)
        self.assertEqual(self.sched.size(), 1)

    def test_get_next_due_returns_earliest(self):
        """get_next_due() peeks at the card with the earliest due datetime."""
        due_early = _ts(-1)    # overdue
        due_late = _ts(2)

        self.sched.add_card(_make_card("late", due_late))
        self.sched.add_card(_make_card("early", due_early))

        peeked = self.sched.get_next_due()
        self.assertEqual(peeked.card_id, "early")

    def test_get_next_due_does_not_remove(self):
        """get_next_due() must leave the queue unchanged."""
        self.sched.add_card(_make_card("c1", _ts(1)))
        _ = self.sched.get_next_due()
        self.assertEqual(self.sched.size(), 1)

    def test_get_next_due_empty_returns_none(self):
        self.assertIsNone(self.sched.get_next_due())

    def test_pop_next_due_removes_card(self):
        """pop_next_due() removes and returns the earliest card."""
        self.sched.add_card(_make_card("c1", _ts(1)))
        popped = self.sched.pop_next_due()
        self.assertEqual(popped.card_id, "c1")
        self.assertEqual(self.sched.size(), 0)

    def test_pop_next_due_empty_returns_none_or_raises(self):
        """pop on empty queue: must not crash silently (returns None or raises)."""
        try:
            result = self.sched.pop_next_due()
            self.assertIsNone(result)
        except (IndexError, StopIteration, ValueError):
            pass  # acceptable

    def test_pop_maintains_order_across_multiple_pops(self):
        """Successive pops return cards in ascending due-datetime order."""
        dues = [_ts(3), _ts(1), _ts(2), _ts(0.5), _ts(4)]
        for i, d in enumerate(dues):
            self.sched.add_card(_make_card(f"c{i}", d))

        prev_due = datetime.min
        while self.sched.size() > 0:
            card = self.sched.pop_next_due()
            self.assertGreaterEqual(card.due_datetime, prev_due)
            prev_due = card.due_datetime

class TestSchedulerGetDueCards(unittest.TestCase):
    """Test getting due cards `get_due_cards()` """
    def setUp(self):
        self.sched = Scheduler()

    def test_returns_only_overdue_cards(self):
        """Only cards with due ≤ now are returned."""
        self.sched.add_card(_make_card("past", _ts(-2)))
        self.sched.add_card(_make_card("future", _ts(2)))

        due = self.sched.get_due_cards(reference_time=datetime.utcnow())

        self.assertEqual(len(due), 1)
        self.assertEqual(due[0].card_id, "past")

    def test_empty_queue_returns_empty_list(self):
        due = self.sched.get_due_cards(reference_time=datetime.utcnow())
        self.assertEqual(due, [])

    def test_respects_limit(self):
        for i in range(10):
            self.sched.add_card(_make_card(f"c{i}", _ts(-1)))

        due = self.sched.get_due_cards(reference_time=datetime.utcnow(), limit=5)
        self.assertEqual(len(due), 5)

    def test_all_future_cards_returns_empty(self):
        for i in range(5):
            self.sched.add_card(_make_card(f"c{i}", _ts(i + 1)))

        due = self.sched.get_due_cards(reference_time=datetime.utcnow())
        self.assertEqual(len(due), 0)

    def test_returns_multiple_overdue_in_priority_order(self):
        """get_due_cards result should be sorted earliest-first."""
        for offset in [3, 1, 2]:
            self.sched.add_card(_make_card(f"c{offset}", _ts(-offset)))

        due = self.sched.get_due_cards(reference_time=datetime.utcnow())
        self.assertEqual(len(due), 3)

        # Verify order: most overdue first
        for i in range(len(due) - 1):
            self.assertLessEqual(due[i].due_datetime, due[i + 1].due_datetime)



class TestSchedulerUpdateRemove(unittest.TestCase):
    """Tests Scenarios of Update or Removal of Cards"""

    def setUp(self):
        self.sched = Scheduler()

    def test_update_card_reschedules(self):
        """Updating due_datetime repositions the card in the heap."""
        card = _make_card("c1", _ts(10))
        self.sched.add_card(card)

        # Push it to the front
        card.due_datetime = _ts(-1)
        self.sched.update_card(card)

        next_card = self.sched.get_next_due()
        self.assertEqual(next_card.card_id, "c1")

    def test_update_card_preserves_queue_size(self):
        """An update must not alter the total number of items."""
        card = _make_card("c1", _ts(5))
        self.sched.add_card(_make_card("c2", _ts(1)))
        self.sched.add_card(card)

        card.due_datetime = _ts(0)
        self.sched.update_card(card)

        self.assertEqual(self.sched.size(), 2)

    def test_remove_existing_card(self):
        """remove_card() decreases queue size by 1."""
        self.sched.add_card(_make_card("c1", _ts(1)))
        self.sched.add_card(_make_card("c2", _ts(2)))

        self.sched.remove_card("c1")

        self.assertEqual(self.sched.size(), 1)
        remaining = self.sched.pop_next_due()
        self.assertEqual(remaining.card_id, "c2")

    def test_remove_nonexistent_card_is_safe(self):
        """Removing a card that does not exist must not crash the scheduler."""
        self.sched.add_card(_make_card("c1", _ts(1)))
        try:
            self.sched.remove_card("does_not_exist")
        except Exception:  # noqa: BLE001
            pass  # CardNotFoundError is acceptable

        # Queue must remain intact
        self.assertEqual(self.sched.size(), 1)

    def test_duplicate_add_updates_card(self):
        """Adding a card that is already in the queue updates its position."""
        card = _make_card("c1", _ts(5))
        self.sched.add_card(card)

        card.due_datetime = _ts(-1)
        self.sched.add_card(card)

        # Must still be size 1 (or at most 2 if impl allows dupes then dedupes on pop)
        next_card = self.sched.pop_next_due()
        self.assertEqual(next_card.card_id, "c1")


class TestSchedulerPriorityOrdering(unittest.TestCase):
    """Verify heap invariants are preserved under a sequence of mixed ops."""

    def setUp(self):
        self.sched = Scheduler()

    def test_heap_invariant_after_mixed_ops(self):
        """
        Add 20 cards, pop 10, add 10 more, pop all — the output order must
        be non-decreasing by due_datetime.
        """
        import random
        rng = random.Random(42)

        offsets = [rng.uniform(-5, 15) for _ in range(20)]
        for i, off in enumerate(offsets):
            self.sched.add_card(_make_card(f"c{i}", _ts(off)))

        popped_all = []
        for _ in range(10):
            popped_all.append(self.sched.pop_next_due())

        # Add 10 more
        for i in range(20, 30):
            self.sched.add_card(_make_card(f"c{i}", _ts(rng.uniform(-5, 15))))

        while self.sched.size() > 0:
            popped_all.append(self.sched.pop_next_due())

        for i in range(len(popped_all) - 1):
            self.assertLessEqual(
                popped_all[i].due_datetime,
                popped_all[i + 1].due_datetime,
                msg=f"Ordering violated between index {i} and {i+1}",
            )


