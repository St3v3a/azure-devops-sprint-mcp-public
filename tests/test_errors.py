"""
Unit tests for error module.

Tests all custom exception classes and error handling.
"""

import pytest
from src.errors import (
    AzureDevOpsError,
    WorkItemNotFoundError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    TransientError,
    QueryTooLargeError
)
from src.validation import ValidationError


class TestAzureDevOpsError:
    """Test base AzureDevOpsError class."""

    def test_base_error_creation(self):
        """Test creating base error with message."""
        error = AzureDevOpsError("Test error message")
        assert str(error) == "Test error message"
        assert error.status_code is None

    def test_base_error_with_status_code(self):
        """Test base error with status code."""
        error = AzureDevOpsError("Test error", status_code=500)
        assert error.status_code == 500
        assert "[500]" in str(error)

    def test_base_error_inheritance(self):
        """Test that base error inherits from Exception."""
        error = AzureDevOpsError("Test")
        assert isinstance(error, Exception)


class TestWorkItemNotFoundError:
    """Test WorkItemNotFoundError (404)."""

    def test_error_with_work_item_id(self):
        """Test error message includes work item ID."""
        error = WorkItemNotFoundError(work_item_id=123)
        assert error.status_code == 404
        assert "123" in str(error)
        assert "not found" in str(error).lower()

    def test_error_without_work_item_id(self):
        """Test error message without specific ID."""
        error = WorkItemNotFoundError()
        assert error.status_code == 404
        assert "not found" in str(error).lower()

    def test_error_inheritance(self):
        """Test inheritance from base error."""
        error = WorkItemNotFoundError(work_item_id=123)
        assert isinstance(error, AzureDevOpsError)


class TestAuthenticationError:
    """Test AuthenticationError (401)."""

    def test_error_default_message(self):
        """Test default authentication error message."""
        error = AuthenticationError()
        assert error.status_code == 401
        assert "authentication failed" in str(error).lower()
        assert "token" in str(error).lower()

    def test_error_custom_message(self):
        """Test custom error message."""
        error = AuthenticationError("Custom auth message")
        assert error.status_code == 401
        assert "Custom auth message" in str(error)

    def test_error_suggestions(self):
        """Test that error message contains helpful suggestions."""
        error = AuthenticationError()
        message = str(error).lower()
        assert "expired" in message or "refresh" in message


class TestPermissionDeniedError:
    """Test PermissionDeniedError (403)."""

    def test_error_default_message(self):
        """Test default permission error message."""
        error = PermissionDeniedError()
        assert error.status_code == 403
        assert "permission denied" in str(error).lower()

    def test_error_with_resource(self):
        """Test error with specific resource."""
        error = PermissionDeniedError(resource="work item 123")
        assert "work item 123" in str(error)

    def test_error_suggestions(self):
        """Test that error contains permission guidance."""
        error = PermissionDeniedError()
        message = str(error).lower()
        assert "permission" in message or "credentials" in message


class TestRateLimitError:
    """Test RateLimitError (429)."""

    def test_error_default(self):
        """Test default rate limit error."""
        error = RateLimitError()
        assert error.status_code == 429
        assert "rate limit" in str(error).lower()

    def test_error_with_retry_after(self):
        """Test error with retry-after header."""
        error = RateLimitError(retry_after=60)
        assert error.retry_after == 60
        assert "60" in str(error)
        assert "retry after" in str(error).lower()

    def test_retry_after_attribute(self):
        """Test that retry_after is accessible as attribute."""
        error = RateLimitError(retry_after=120)
        assert error.retry_after == 120
        assert hasattr(error, 'retry_after')

    def test_error_without_retry_after(self):
        """Test error without retry-after value."""
        error = RateLimitError()
        assert error.retry_after is None


class TestTransientError:
    """Test TransientError (500-504)."""

    def test_error_with_status_500(self):
        """Test transient error with 500 status."""
        error = TransientError(status_code=500)
        assert error.status_code == 500
        assert "temporarily unavailable" in str(error).lower()

    def test_error_with_status_502(self):
        """Test transient error with 502 status."""
        error = TransientError(status_code=502)
        assert error.status_code == 502
        assert "502" in str(error)

    def test_error_with_status_503(self):
        """Test transient error with 503 status."""
        error = TransientError(status_code=503)
        assert error.status_code == 503
        assert "503" in str(error)

    def test_error_with_status_504(self):
        """Test transient error with 504 status."""
        error = TransientError(status_code=504)
        assert error.status_code == 504
        assert "timeout" in str(error).lower()

    def test_error_suggestions(self):
        """Test that error suggests automatic retry."""
        error = TransientError(status_code=503)
        message = str(error).lower()
        assert "retry" in message or "temporary" in message


class TestValidationError:
    """Test ValidationError."""

    def test_error_with_field(self):
        """Test validation error with field name."""
        error = ValidationError("Invalid value", field_name="System.State")
        assert "System.State" in str(error)
        assert "Invalid value" in str(error)

    def test_error_without_field(self):
        """Test validation error without field name."""
        error = ValidationError("Invalid input")
        assert "Invalid input" in str(error)

    def test_error_with_allowed_values(self):
        """Test error with list of allowed values."""
        error = ValidationError(
            "Invalid state",
            field_name="System.State",
            allowed_values=['Active', 'Closed']
        )
        assert "Active" in str(error)
        assert "Closed" in str(error)

    def test_field_attribute_accessible(self):
        """Test that field_name is accessible as attribute."""
        error = ValidationError("Test", field_name="Test.Field")
        assert error.field_name == "Test.Field"
        assert hasattr(error, 'allowed_values')


class TestQueryTooLargeError:
    """Test QueryTooLargeError (413)."""

    def test_error_with_counts(self):
        """Test error with result and max counts."""
        error = QueryTooLargeError(result_count=25000, max_results=20000)
        assert error.status_code == 413
        assert "25000" in str(error) or "25,000" in str(error)
        assert "20000" in str(error) or "20,000" in str(error)

    def test_error_without_counts(self):
        """Test error without specific counts."""
        error = QueryTooLargeError()
        assert error.status_code == 413
        assert "too large" in str(error).lower()

    def test_error_suggestions(self):
        """Test that error suggests solutions."""
        error = QueryTooLargeError(result_count=25000, max_results=20000)
        message = str(error).lower()
        assert "limit" in message or "filter" in message or "reduce" in message

    def test_result_count_attribute(self):
        """Test that result_count is accessible."""
        error = QueryTooLargeError(result_count=30000, max_results=20000)
        assert error.result_count == 30000
        assert error.max_results == 20000


class TestErrorFormatting:
    """Test error message formatting."""

    def test_status_code_in_message(self):
        """Test that status codes appear in brackets."""
        error = AzureDevOpsError("Test", status_code=404)
        assert "[404]" in str(error)

    def test_message_without_status_code(self):
        """Test messages without status codes."""
        error = AzureDevOpsError("Test message")
        assert str(error) == "Test message"
        assert "[" not in str(error)

    def test_multiline_messages(self):
        """Test that multiline messages are preserved."""
        message = "Line 1\nLine 2\nLine 3"
        error = AzureDevOpsError(message)
        assert "Line 1" in str(error)
        assert "Line 2" in str(error)
        assert "Line 3" in str(error)


class TestErrorUsage:
    """Test error usage patterns."""

    def test_error_can_be_raised(self):
        """Test that errors can be raised and caught."""
        with pytest.raises(WorkItemNotFoundError):
            raise WorkItemNotFoundError(work_item_id=123)

    def test_error_can_be_caught_as_base_type(self):
        """Test that specific errors can be caught as base type."""
        with pytest.raises(AzureDevOpsError):
            raise WorkItemNotFoundError(work_item_id=123)

    def test_error_can_be_caught_as_exception(self):
        """Test that errors can be caught as generic Exception."""
        with pytest.raises(Exception):
            raise RateLimitError(retry_after=60)

    def test_multiple_error_types(self):
        """Test catching multiple error types."""
        errors = [
            WorkItemNotFoundError(work_item_id=1),
            AuthenticationError(),
            RateLimitError(retry_after=30),
            TransientError(status_code=503)
        ]

        for error in errors:
            with pytest.raises(AzureDevOpsError):
                raise error


class TestErrorAttributes:
    """Test that errors have expected attributes."""

    def test_all_errors_have_status_code(self):
        """Test that all errors have status_code attribute."""
        errors = [
            WorkItemNotFoundError(),
            AuthenticationError(),
            PermissionDeniedError(),
            RateLimitError(),
            TransientError(status_code=500),
            QueryTooLargeError()
        ]

        for error in errors:
            assert hasattr(error, 'status_code')
            assert error.status_code is not None

    def test_validation_errors_have_field_name(self):
        """Test that validation errors have field_name attribute."""
        errors = [
            ValidationError("Test", field_name="Field"),
            InvalidStateError(state="Test"),
            InvalidFieldError(field_name="Test")
        ]

        for error in errors:
            assert hasattr(error, 'field_name')

    def test_rate_limit_has_retry_after(self):
        """Test that RateLimitError has retry_after attribute."""
        error = RateLimitError(retry_after=60)
        assert hasattr(error, 'retry_after')
        assert error.retry_after == 60

    def test_query_too_large_has_counts(self):
        """Test that QueryTooLargeError has count attributes."""
        error = QueryTooLargeError(result_count=1000, max_results=500)
        assert hasattr(error, 'result_count')
        assert hasattr(error, 'max_results')
        assert error.result_count == 1000
        assert error.max_results == 500
