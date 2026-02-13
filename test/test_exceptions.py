"""
Unit tests for sp_quiz.core.exceptions module.

Tests cover:
- Exception hierarchy
- Error codes
- Exception messages
- Inheritance from base exception
- Exception raising and catching
- Edge cases
- Documentation compliance (PEP 257)
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sp_quiz.core.exceptions import (
    SpQuizError,
    CardNotFoundError,
    InvalidCardStateError,
    SessionNotFoundError,
    SessionClosedError,
    InvalidQualityRatingError,
    StorageError,
    ConcurrencyError
)


class TestBaseException(unittest.TestCase):
    """Test SpQuizError base exception."""
    
    def test_base_exception_inheritance(self):
        """Test SpQuizError inherits from Exception."""
        self.assertTrue(issubclass(SpQuizError, Exception))
    
    def test_base_exception_can_be_raised(self):
        """Test SpQuizError can be raised."""
        with self.assertRaises(SpQuizError):
            raise SpQuizError("Test error")
    
    def test_base_exception_with_message(self):
        """Test SpQuizError with custom message."""
        message = "Custom error message"
        try:
            raise SpQuizError(message)
        except SpQuizError as e:
            self.assertEqual(str(e), message)
    
    def test_base_exception_without_message(self):
        """Test SpQuizError without message."""
        try:
            raise SpQuizError()
        except SpQuizError as e:
            self.assertIsNotNone(str(e))
    
    def test_base_exception_has_docstring(self):
        """Test SpQuizError has docstring."""
        self.assertIsNotNone(SpQuizError.__doc__)
        self.assertTrue(len(SpQuizError.__doc__) > 0)


class TestCardNotFoundError(unittest.TestCase):
    """Test CardNotFoundError exception."""
    
    def test_inheritance_from_base(self):
        """Test CardNotFoundError inherits from SpQuizError."""
        self.assertTrue(issubclass(CardNotFoundError, SpQuizError))
    
    def test_can_be_raised(self):
        """Test CardNotFoundError can be raised."""
        with self.assertRaises(CardNotFoundError):
            raise CardNotFoundError("Card not found")
    
    def test_caught_as_base_exception(self):
        """Test CardNotFoundError can be caught as SpQuizError."""
        with self.assertRaises(SpQuizError):
            raise CardNotFoundError("Card not found")
    
    def test_error_code(self):
        """Test CardNotFoundError has correct error code."""
        self.assertEqual(CardNotFoundError.code, 'CARD_001')
    
    def test_with_card_id_message(self):
        """Test CardNotFoundError with card ID in message."""
        card_id = "card_12345"
        try:
            raise CardNotFoundError(f"Card {card_id} not found")
        except CardNotFoundError as e:
            self.assertIn(card_id, str(e))
    
    def test_has_docstring(self):
        """Test CardNotFoundError has docstring."""
        self.assertIsNotNone(CardNotFoundError.__doc__)


class TestInvalidCardStateError(unittest.TestCase):
    """Test InvalidCardStateError exception."""
    
    def test_inheritance_from_base(self):
        """Test InvalidCardStateError inherits from SpQuizError."""
        self.assertTrue(issubclass(InvalidCardStateError, SpQuizError))
    
    def test_can_be_raised(self):
        """Test InvalidCardStateError can be raised."""
        with self.assertRaises(InvalidCardStateError):
            raise InvalidCardStateError("Invalid state transition")
    
    def test_error_code(self):
        """Test InvalidCardStateError has correct error code."""
        self.assertEqual(InvalidCardStateError.code, 'CARD_002')
    
    def test_with_state_information(self):
        """Test InvalidCardStateError with state information."""
        message = "Cannot transition from NEW to SUSPENDED"
        try:
            raise InvalidCardStateError(message)
        except InvalidCardStateError as e:
            self.assertEqual(str(e), message)
    
    def test_has_docstring(self):
        """Test InvalidCardStateError has docstring."""
        self.assertIsNotNone(InvalidCardStateError.__doc__)


class TestSessionNotFoundError(unittest.TestCase):
    """Test SessionNotFoundError exception."""
    
    def test_inheritance_from_base(self):
        """Test SessionNotFoundError inherits from SpQuizError."""
        self.assertTrue(issubclass(SessionNotFoundError, SpQuizError))
    
    def test_can_be_raised(self):
        """Test SessionNotFoundError can be raised."""
        with self.assertRaises(SessionNotFoundError):
            raise SessionNotFoundError("Session not found")
    
    def test_error_code(self):
        """Test SessionNotFoundError has correct error code."""
        self.assertEqual(SessionNotFoundError.code, 'SESSION_001')
    
    def test_with_session_id(self):
        """Test SessionNotFoundError with session ID."""
        session_id = "session_xyz"
        try:
            raise SessionNotFoundError(f"Session {session_id} not found")
        except SessionNotFoundError as e:
            self.assertIn(session_id, str(e))
    
    def test_has_docstring(self):
        """Test SessionNotFoundError has docstring."""
        self.assertIsNotNone(SessionNotFoundError.__doc__)


class TestSessionClosedError(unittest.TestCase):
    """Test SessionClosedError exception."""
    
    def test_inheritance_from_base(self):
        """Test SessionClosedError inherits from SpQuizError."""
        self.assertTrue(issubclass(SessionClosedError, SpQuizError))
    
    def test_can_be_raised(self):
        """Test SessionClosedError can be raised."""
        with self.assertRaises(SessionClosedError):
            raise SessionClosedError("Session is closed")
    
    def test_error_code(self):
        """Test SessionClosedError has correct error code."""
        self.assertEqual(SessionClosedError.code, 'SESSION_002')
    
    def test_with_operation_context(self):
        """Test SessionClosedError with operation context."""
        message = "Cannot get next card from closed session"
        try:
            raise SessionClosedError(message)
        except SessionClosedError as e:
            self.assertIn("closed", str(e).lower())
    
    def test_has_docstring(self):
        """Test SessionClosedError has docstring."""
        self.assertIsNotNone(SessionClosedError.__doc__)


class TestInvalidQualityRatingError(unittest.TestCase):
    """Test InvalidQualityRatingError exception."""
    
    def test_inheritance_from_base(self):
        """Test InvalidQualityRatingError inherits from SpQuizError."""
        self.assertTrue(issubclass(InvalidQualityRatingError, SpQuizError))
    
    def test_can_be_raised(self):
        """Test InvalidQualityRatingError can be raised."""
        with self.assertRaises(InvalidQualityRatingError):
            raise InvalidQualityRatingError("Quality must be 0-5")
    
    def test_error_code(self):
        """Test InvalidQualityRatingError has correct error code."""
        self.assertEqual(InvalidQualityRatingError.code, 'REVIEW_001')
    
    def test_with_invalid_quality_value(self):
        """Test InvalidQualityRatingError with invalid value."""
        invalid_quality = 10
        try:
            raise InvalidQualityRatingError(f"Quality {invalid_quality} is invalid")
        except InvalidQualityRatingError as e:
            self.assertIn(str(invalid_quality), str(e))
    
    def test_has_docstring(self):
        """Test InvalidQualityRatingError has docstring."""
        self.assertIsNotNone(InvalidQualityRatingError.__doc__)


class TestStorageError(unittest.TestCase):
    """Test StorageError exception."""
    
    def test_inheritance_from_base(self):
        """Test StorageError inherits from SpQuizError."""
        self.assertTrue(issubclass(StorageError, SpQuizError))
    
    def test_can_be_raised(self):
        """Test StorageError can be raised."""
        with self.assertRaises(StorageError):
            raise StorageError("Storage operation failed")
    
    def test_error_code(self):
        """Test StorageError has correct error code."""
        self.assertEqual(StorageError.code, 'STORAGE_001')
    
    def test_with_storage_details(self):
        """Test StorageError with storage operation details."""
        message = "Failed to write to file: permission denied"
        try:
            raise StorageError(message)
        except StorageError as e:
            self.assertIn("Failed", str(e))
    
    def test_has_docstring(self):
        """Test StorageError has docstring."""
        self.assertIsNotNone(StorageError.__doc__)


class TestConcurrencyError(unittest.TestCase):
    """Test ConcurrencyError exception."""
    
    def test_inheritance_from_base(self):
        """Test ConcurrencyError inherits from SpQuizError."""
        self.assertTrue(issubclass(ConcurrencyError, SpQuizError))
    
    def test_can_be_raised(self):
        """Test ConcurrencyError can be raised."""
        with self.assertRaises(ConcurrencyError):
            raise ConcurrencyError("Concurrent modification detected")
    
    def test_error_code(self):
        """Test ConcurrencyError has correct error code."""
        self.assertEqual(ConcurrencyError.code, 'CONCURRENCY_001')
    
    def test_with_conflict_details(self):
        """Test ConcurrencyError with conflict details."""
        message = "Card was modified by another operation"
        try:
            raise ConcurrencyError(message)
        except ConcurrencyError as e:
            self.assertIn("modified", str(e).lower())
    
    def test_has_docstring(self):
        """Test ConcurrencyError has docstring."""
        self.assertIsNotNone(ConcurrencyError.__doc__)


class TestExceptionHierarchy(unittest.TestCase):
    """Test exception hierarchy relationships."""
    
    def test_all_exceptions_inherit_from_base(self):
        """Test all custom exceptions inherit from SpQuizError."""
        exceptions = [
            CardNotFoundError,
            InvalidCardStateError,
            SessionNotFoundError,
            SessionClosedError,
            InvalidQualityRatingError,
            StorageError,
            ConcurrencyError
        ]
        
        for exc_class in exceptions:
            self.assertTrue(
                issubclass(exc_class, SpQuizError),
                f"{exc_class.__name__} should inherit from SpQuizError"
            )
    
    def test_all_exceptions_are_exceptions(self):
        """Test all custom exceptions are Exception instances."""
        exceptions = [
            SpQuizError,
            CardNotFoundError,
            InvalidCardStateError,
            SessionNotFoundError,
            SessionClosedError,
            InvalidQualityRatingError,
            StorageError,
            ConcurrencyError
        ]
        
        for exc_class in exceptions:
            self.assertTrue(
                issubclass(exc_class, Exception),
                f"{exc_class.__name__} should be an Exception"
            )
    
    def test_catch_all_with_base(self):
        """Test catching all custom exceptions with base class."""
        exceptions_to_test = [
            CardNotFoundError("test"),
            InvalidCardStateError("test"),
            SessionNotFoundError("test"),
            SessionClosedError("test"),
            InvalidQualityRatingError("test"),
            StorageError("test"),
            ConcurrencyError("test")
        ]
        
        for exc in exceptions_to_test:
            with self.assertRaises(SpQuizError):
                raise exc


class TestErrorCodes(unittest.TestCase):
    """Test error code system."""
    
    def test_all_exceptions_have_codes(self):
        """Test all exceptions have error codes defined."""
        exceptions = [
            CardNotFoundError,
            InvalidCardStateError,
            SessionNotFoundError,
            SessionClosedError,
            InvalidQualityRatingError,
            StorageError,
            ConcurrencyError
        ]
        
        for exc_class in exceptions:
            self.assertTrue(
                hasattr(exc_class, 'code'),
                f"{exc_class.__name__} should have a 'code' attribute"
            )
            self.assertIsNotNone(
                exc_class.code,
                f"{exc_class.__name__}.code should not be None"
            )
    
    def test_error_codes_are_unique(self):
        """Test all error codes are unique."""
        exceptions = [
            CardNotFoundError,
            InvalidCardStateError,
            SessionNotFoundError,
            SessionClosedError,
            InvalidQualityRatingError,
            StorageError,
            ConcurrencyError
        ]
        
        codes = [exc.code for exc in exceptions]
        self.assertEqual(len(codes), len(set(codes)), "Error codes should be unique")
    
    def test_error_code_format(self):
        """Test error codes follow expected format."""
        exceptions = [
            CardNotFoundError,
            InvalidCardStateError,
            SessionNotFoundError,
            SessionClosedError,
            InvalidQualityRatingError,
            StorageError,
            ConcurrencyError
        ]
        
        for exc_class in exceptions:
            code = exc_class.code
            self.assertIsInstance(code, str)
            self.assertTrue(len(code) > 0)
            # Format should be PREFIX_NUMBER (e.g., CARD_001)
            parts = code.split('_')
            self.assertEqual(len(parts), 2, f"Code {code} should have format PREFIX_NUMBER")
            self.assertTrue(parts[1].isdigit(), f"Code {code} should end with digits")


class TestExceptionUsage(unittest.TestCase):
    """Test practical exception usage scenarios."""
    
    def test_exception_with_multiple_args(self):
        """Test exceptions with multiple arguments."""
        try:
            raise CardNotFoundError("Card not found", "card_123")
        except CardNotFoundError as e:
            self.assertIn("Card not found", str(e))
    
    def test_exception_chaining(self):
        """Test exception chaining (raise from)."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise StorageError("Storage failed") from e
        except StorageError as e:
            self.assertIsNotNone(e.__cause__)
            self.assertIsInstance(e.__cause__, ValueError)
    
    def test_exception_with_empty_message(self):
        """Test exceptions with empty message."""
        try:
            raise SessionNotFoundError("")
        except SessionNotFoundError as e:
            # Should not crash
            str_repr = str(e)
            self.assertIsInstance(str_repr, str)
    
    def test_exception_in_context_manager(self):
        """Test exceptions work in context managers."""
        caught = False
        try:
            with self.assertRaises(InvalidQualityRatingError):
                raise InvalidQualityRatingError("Invalid quality")
            caught = True
        except Exception:
            self.fail("Exception should have been caught by assertRaises")
        
        self.assertTrue(caught)
    
    def test_multiple_exception_handling(self):
        """Test handling multiple exception types."""
        def raise_random_error(error_type):
            if error_type == 1:
                raise CardNotFoundError("Card error")
            elif error_type == 2:
                raise SessionNotFoundError("Session error")
            else:
                raise StorageError("Storage error")
        
        # Test each can be caught specifically
        for error_type in [1, 2, 3]:
            with self.assertRaises(SpQuizError):
                raise_random_error(error_type)


class TestExceptionStringRepresentation(unittest.TestCase):
    """Test exception string representations."""
    
    def test_exception_str(self):
        """Test exception __str__ method."""
        message = "Test error message"
        exc = CardNotFoundError(message)
        
        self.assertEqual(str(exc), message)
    
    def test_exception_repr(self):
        """Test exception __repr__ method."""
        message = "Test error"
        exc = SessionClosedError(message)
        
        repr_str = repr(exc)
        self.assertIn("SessionClosedError", repr_str)
    
    def test_unicode_error_message(self):
        """Test exceptions with Unicode messages."""
        message = "Error: 카드를 찾을 수 없습니다"
        exc = CardNotFoundError(message)
        
        self.assertEqual(str(exc), message)


if __name__ == '__main__':
    unittest.main(verbosity=2)
