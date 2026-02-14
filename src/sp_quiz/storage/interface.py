"""
Abstract storage interface for sp-quiz persistence layer.

This module defines the abstract base class that all storage implementations
must inherit from. It is a consistent API for data persistence.

Classes:
    StorageInterface: Abstract base class for storage implementations
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from sp_quiz.core.card import Card
from sp_quiz.core.review import Review
from sp_quiz.core.user import UserProgress


class StorageInterface(ABC):
    """
    Abstract base class defining the storage interface for sp-quiz.
    
    All storage implementations (in-memory, file-based, database, etc.)
    must inherit from this class and implement all abstract methods.
    
    This ensures a consistent API across different storage backends and
    allows for easy swapping of storage implementations.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_user_progress(self, user_id: str) -> Optional[UserProgress]:
        """
        Retrieve user progress statistics.
        
        Args:
            user_id: Unique identifier of the user
            
        Returns:
            UserProgress instance if exists, None otherwise
            
        Raises:
            StorageError: If retrieval operation fails
        """
        pass
    
    @abstractmethod
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
        pass
