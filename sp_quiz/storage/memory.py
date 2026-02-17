"""
In-memory storage implementation for sp-quiz.

This module provides a thread-safe in-memory storage implementation
suitable for testing, development, and single-instance deployments.

Classes:
    InMemoryStorage: Thread-safe in-memory storage implementation
"""

import threading
from typing import List, Optional, Dict
from copy import deepcopy

from sp_quiz.storage.interface import StorageInterface
from sp_quiz.core.card import Card
from sp_quiz.core.review import Review
from sp_quiz.core.user import UserProgress
from sp_quiz.core.exceptions import CardNotFoundError, StorageError


class InMemoryStorage(StorageInterface):
    """
    Thread-safe in-memory storage implementation.
    
    Stores all data in memory using dictionaries. All operations are
    protected by locks to ensure thread safety in multi-threaded
    environments.
    
    For Now, This is a Dev implementation that is suitable for:
    - Development and testing
    - Single-instance applications
    - Scenarios where data persistence is not required
    
    Note: All data is lost when the process terminates.
    """
    
    def __init__(self):
        """Initialize empty in-memory storage with thread locks."""
        self._cards: Dict[str, Card] = {}
        self._reviews: List[Review] = []
        self._user_progress: Dict[str, UserProgress] = {}
        
        # Thread safety locks
        self._cards_lock = threading.RLock()
        self._reviews_lock = threading.RLock()
        self._progress_lock = threading.RLock()
    
    def save_card(self, card: Card) -> Card:
        """
        Save a new card to storage.
        
        Args:
            card: Card instance to save
            
        Returns:
            The saved Card instance
            
        Raises:
            StorageError: If save operation fails
        """
        with self._cards_lock:
            try:
                # Store a copy to prevent external modifications
                self._cards[card.card_id] = deepcopy(card)
                return deepcopy(card)
            except Exception as e:
                raise StorageError(f"Failed to save card: {e}")
    
    def get_card(self, card_id: str) -> Card:
        """
        Retrieve a card by its ID.
        
        Args:
            card_id: Unique identifier of the card
            
        Returns:
            The Card instance
            
        Raises:
            CardNotFoundError: If card does not exist
            StorageError: If retrieval operation fails
        """
        with self._cards_lock:
            try:
                if card_id not in self._cards:
                    raise CardNotFoundError(f"Card {card_id} not found")
                # Return a copy to prevent external modifications
                return deepcopy(self._cards[card_id])
            except CardNotFoundError:
                raise
            except Exception as e:
                raise StorageError(f"Failed to retrieve card: {e}")
    
    def update_card(self, card: Card) -> Card:
        """
        Update an existing card in storage.
        
        Args:
            card: Card instance with updated data
            
        Returns:
            The updated Card instance
            
        Raises:
            CardNotFoundError: If card does not exist
            StorageError: If update operation fails
        """
        with self._cards_lock:
            try:
                if card.card_id not in self._cards:
                    raise CardNotFoundError(f"Card {card.card_id} not found")
                # Store a copy to prevent external modifications
                self._cards[card.card_id] = deepcopy(card)
                return deepcopy(card)
            except CardNotFoundError:
                raise
            except Exception as e:
                raise StorageError(f"Failed to update card: {e}")
    
    def delete_card(self, card_id: str) -> bool:
        """
        Delete a card from storage.
        
        Args:
            card_id: Unique identifier of the card to delete
            
        Returns:
            True if card was deleted, False if card did not exist
            
        Raises:
            StorageError: If delete operation fails
        """
        with self._cards_lock:
            try:
                if card_id in self._cards:
                    del self._cards[card_id]
                    return True
                return False
            except Exception as e:
                raise StorageError(f"Failed to delete card: {e}")
    
    def get_user_cards(self, user_id: str) -> List[Card]:
        """
        Retrieve all cards for a specific user.
        
        Args:
            user_id: Unique identifier of the user
            
        Returns:
            List of Card instances (empty list if user has no cards)
            
        Raises:
            StorageError: If retrieval operation fails
        """
        with self._cards_lock:
            try:
                user_cards = [
                    deepcopy(card) for card in self._cards.values()
                    if card.user_id == user_id
                ]
                return user_cards
            except Exception as e:
                raise StorageError(f"Failed to retrieve user cards: {e}")
    
    def save_review(self, review: Review) -> Review:
        """
        Save a review record to storage.
        
        Args:
            review: Review instance to save
            
        Returns:
            The saved Review instance
            
        Raises:
            StorageError: If save operation fails
        """
        with self._reviews_lock:
            try:
                # Store a copy to prevent external modifications
                self._reviews.append(deepcopy(review))
                return deepcopy(review)
            except Exception as e:
                raise StorageError(f"Failed to save review: {e}")
    
    def get_reviews(self, card_id: Optional[str] = None,
                   user_id: Optional[str] = None,
                   session_id: Optional[str] = None) -> List[Review]:
        """
        Retrieve reviews filtered by optional criteria.
        
        Args:
            card_id: Optional card ID to filter by
            user_id: Optional user ID to filter by
            session_id: Optional session ID to filter by
            
        Returns:
            List of Review instances matching the filters
            
        Raises:
            StorageError: If retrieval operation fails
        """
        with self._reviews_lock:
            try:
                filtered_reviews = self._reviews
                
                # Apply filters
                if card_id is not None:
                    filtered_reviews = [r for r in filtered_reviews if r.card_id == card_id]
                
                if user_id is not None:
                    filtered_reviews = [r for r in filtered_reviews if r.user_id == user_id]
                
                if session_id is not None:
                    filtered_reviews = [r for r in filtered_reviews if r.session_id == session_id]
                
                # Return copies to prevent external modifications
                return [deepcopy(r) for r in filtered_reviews]
            except Exception as e:
                raise StorageError(f"Failed to retrieve reviews: {e}")
    
    def get_user_progress(self, user_id: str) -> Optional[UserProgress]:
        """
        Retrieve user progress statistics.
        
        Creates a default UserProgress instance for new users if one doesn't exist.
        
        Args:
            user_id: Unique identifier of the user
            
        Returns:
            UserProgress instance (creates default for new users)
            
        Raises:
            StorageError: If retrieval operation fails
        """
        with self._progress_lock:
            try:
                if user_id not in self._user_progress:
                    # Create default progress for new users
                    default_progress = UserProgress(user_id=user_id)
                    self._user_progress[user_id] = default_progress
                
                return deepcopy(self._user_progress[user_id])
            except Exception as e:
                raise StorageError(f"Failed to retrieve user progress: {e}")
    
    def update_user_progress(self, progress: UserProgress) -> UserProgress:
        """
        Update user progress statistics.
        
        Args:
            progress: UserProgress instance with updated data
            
        Returns:
            The updated UserProgress instance
            
        Raises:
            StorageError: If update operation fails
        """
        with self._progress_lock:
            try:
                # Store a copy to prevent external modifications
                self._user_progress[progress.user_id] = deepcopy(progress)
                return deepcopy(progress)
            except Exception as e:
                raise StorageError(f"Failed to update user progress: {e}")
