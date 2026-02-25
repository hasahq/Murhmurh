"""
Priority Queue Scheduler for Card Reviews

Manages scheduling of cards for review using a min-heap priority queue
ordered by due datetime. Provides O(log n) insertion and O(1) peek operations.

Classes:
    Scheduler: Priority queue scheduler for card reviews

Features:
    - Efficient priority queue using heapq
    - Thread-safe operations with internal locking
    - Anti-clustering fuzz factor
    - Batch operations for due cards
"""

import heapq
import random
import threading
from datetime import datetime, timedelta
from typing import List, Optional

from ..core.card import Card


class Scheduler:
    """
    Priority queue scheduler for managing card review scheduling.
    
    Uses a min-heap to efficiently manage cards ordered by due datetime.
    Supports concurrent access through internal locking.
    
    Attributes:
        _heap: Internal min-heap of (due_datetime, card_id, card) tuples
        _card_map: Dictionary mapping card_id to card for O(1) lookup
        _lock: Threading lock for concurrent access
    
    Methods:
        add_card: Add or update card in queue
        get_next_due: Peek at next due card
        pop_next_due: Remove and return next due card
        get_due_cards: Get all cards due by reference time
        update_card: Update existing card's position
        remove_card: Remove card from queue
        size: Get current queue size
        apply_fuzz: Add random jitter to due datetime
    """
    def __init__(self):
        """Initialize Empty Scheduler"""
        self._heap: List[tuple] = []
        self._card_map: dict = {}
        self._lock = threading.RLock()
    
    def add_card(self, card: Card) -> None:
        """
        Add card to scheduler or update if already present.
        
        If card already exists (by card_id), removes old entry and adds new.
        Maintains heap property through heappush.
        
        Args:
            card: Card to add/update
        
        Complexity: O(n) for update, O(log n) for new card
        """
        with self._lock:
            # If card exists, rebuild heap without it
            if card.card_id in self._card_map:
                del self._card_map[card.card_id]
                self._heap = [(due, cid, c) for due, cid, c in self._heap 
                             if cid != card.card_id]
                heapq.heapify(self._heap)
            
            # Add to heap
            due = card.due_datetime if card.due_datetime else datetime.utcnow()
            entry = (due, card.card_id, card)
            heapq.heappush(self._heap, entry)
            self._card_map[card.card_id] = card

    def get_next_due(self) -> Optional[Card]:
        """
        Peek at next due card without removing it.
        
        Returns:
            Next due card or None if queue empty
        
        Complexity: O(1) amortized
        """
        with self._lock:
            # Clean up removed cards at top
            while self._heap:
                due, card_id, card = self._heap[0]
                if card_id in self._card_map:
                    return card  # Return card from heap, not map
                # Card was removed, pop it
                heapq.heappop(self._heap)
            
            return None
    
    def pop_next_due(self) -> Optional[Card]:
        """
        Remove and return next due card.
        
        Returns:
            Next due card or None if queue empty
        
        Complexity: O(log n) amortized
        """
        with self._lock:
            # Clean up removed cards
            while self._heap:
                due, card_id, card = heapq.heappop(self._heap)
                if card_id in self._card_map:
                    del self._card_map[card_id]
                    return card
            
            return None
    
    def get_due_cards(self, reference_time: Optional[datetime] = None,
                      limit: Optional[int] = None) -> List[Card]:
        """
        Get all cards due by reference time.
        
        Returns cards in priority order (earliest due first) without
        removing them from the queue.
        
        Args:
            reference_time: Time to check against (default: now)
            limit: Maximum number of cards to return (default: unlimited)
        
        Returns:
            List of due cards ordered by due datetime
        
        Complexity: O(n) where n is number of due cards
        """
        if reference_time is None:
            reference_time = datetime.utcnow()
        
        with self._lock:
            due_cards = []
            
            # Collect all due cards
            for due, card_id, card in self._heap:
                if card_id not in self._card_map:
                    continue  # Skip removed cards
                
                if due <= reference_time:
                    due_cards.append(card)
                    if limit and len(due_cards) >= limit:
                        break
            
            # Sort by due datetime (should already be mostly sorted)
            due_cards.sort(key=lambda c: c.due_datetime if c.due_datetime else datetime.min)
            
            return due_cards
    
    def update_card(self, card: Card) -> None:
        """
        Update card's position in queue.
        
        Equivalent to remove + add, but provided as convenience method.
        
        Args:
            card: Card with updated due_datetime
        
        Complexity: O(log n)
        """
        with self._lock:
            self.add_card(card)
    
    def remove_card(self, card_id: str) -> None:
        """
        Remove card from scheduler by card_id.
        
        Marks card as removed in card_map. Physical removal happens lazily
        during pop or peek operations.
        
        Args:
            card_id: ID of card to remove
        
        Complexity: O(1) amortized
        
        Notes:
            Card is not immediately removed from heap (lazy deletion).
            Heap will be cleaned up during subsequent operations.
        """
        with self._lock:
            if card_id in self._card_map:
                del self._card_map[card_id]
    
    def size(self) -> int:
        """
        Get number of cards currently in scheduler.
        
        Returns:
            Count of active cards (excluding removed)
        
        Complexity: O(1)
        """
        with self._lock:
            return len(self._card_map)
    
    def apply_fuzz(self, scheduled_due: datetime, interval_days: float,
                   fuzz_factor: float = 1.0) -> datetime:
        """
        Apply random jitter to scheduled due datetime.
        
        Prevents cards from clustering by adding random offset:
        - fuzz_range = min(interval × 0.05, 2 days)
        - actual_due = scheduled_due ± uniform(0, fuzz_range)
        
        This spreads reviews more evenly over time.
        
        Args:
            scheduled_due: Original scheduled due datetime
            interval_days: Review interval in days
            fuzz_factor: Fuzz multiplier (0.0 = no fuzz, 1.0 = full fuzz)
        
        Returns:
            Fuzzed due datetime
        
        Examples:
            >>> sched = Scheduler()
            >>> due = datetime(2024, 1, 1, 12, 0)
            >>> fuzzed = sched.apply_fuzz(due, 10.0)  # ±0.5 days
            >>> abs((fuzzed - due).total_seconds()) <= 0.5 * 86400
            True
            >>> sched.apply_fuzz(due, 10.0, fuzz_factor=0.0) == due
            True
        """
        if fuzz_factor == 0.0:
            return scheduled_due
        
        # Calculate fuzz range (max 2 days)
        fuzz_range = min(interval_days * 0.05, 2.0) * fuzz_factor
        
        # Random offset in range [-fuzz_range, +fuzz_range]
        offset_days = random.uniform(-fuzz_range, fuzz_range)
        
        return scheduled_due + timedelta(days=offset_days)
