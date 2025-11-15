"""
Custom exception classes for Azure DevOps MCP server.

Provides structured error handling with helpful messages for common
Azure DevOps API errors.
"""

from typing import Optional, Any


class AzureDevOpsError(Exception):
    """
    Base exception for Azure DevOps API errors.

    Attributes:
        status_code: HTTP status code from the API response
        message: Human-readable error message
        original_error: The original exception that was caught
        details: Additional error details
    """

    def __init__(
        self,
        status_code: Optional[int] = None,
        message: str = "Azure DevOps API error",
        original_error: Optional[Exception] = None,
        details: Optional[Any] = None
    ):
        self.status_code = status_code
        self.message = message
        self.original_error = original_error
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        """String representation of the error."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message

    def to_dict(self) -> dict:
        """Convert error to dictionary for JSON serialization."""
        return {
            'error': self.__class__.__name__,
            'status_code': self.status_code,
            'message': self.message,
            'details': str(self.details) if self.details else None
        }


class WorkItemNotFoundError(AzureDevOpsError):
    """
    Raised when a work item is not found (HTTP 404).

    This can occur when:
    - The work item ID doesn't exist
    - The work item was deleted
    - User doesn't have permission to view the work item
    """

    def __init__(
        self,
        work_item_id: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        message = "Work item not found. Please verify the ID exists and you have access."
        if work_item_id:
            message = f"Work item {work_item_id} not found. Please verify it exists and you have access."

        super().__init__(
            status_code=404,
            message=message,
            original_error=original_error,
            details={'work_item_id': work_item_id} if work_item_id else None
        )


class AuthenticationError(AzureDevOpsError):
    """
    Raised when authentication fails (HTTP 401).

    This can occur when:
    - Token has expired
    - Token is invalid
    - Token is missing required scopes
    """

    def __init__(
        self,
        message: str = "Authentication failed. Your token may have expired. Please refresh credentials.",
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            status_code=401,
            message=message,
            original_error=original_error
        )


class PermissionDeniedError(AzureDevOpsError):
    """
    Raised when user lacks permission for an operation (HTTP 403).

    This can occur when:
    - Token lacks required scopes (e.g., vso.work_write)
    - User doesn't have project permissions
    - Area path restrictions apply
    """

    def __init__(
        self,
        operation: Optional[str] = None,
        required_scope: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        if operation and required_scope:
            message = (
                f"Permission denied for {operation}. "
                f"Your credentials need '{required_scope}' scope for this operation."
            )
        elif operation:
            message = f"Permission denied for {operation}. Please check your project permissions."
        else:
            message = "Permission denied. Please check your credentials and project permissions."

        super().__init__(
            status_code=403,
            message=message,
            original_error=original_error,
            details={'operation': operation, 'required_scope': required_scope}
        )


class RateLimitError(AzureDevOpsError):
    """
    Raised when API rate limit is exceeded (HTTP 429).

    Azure DevOps enforces rate limits to protect service availability.
    This error includes retry-after information.
    """

    def __init__(
        self,
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        if retry_after:
            message = f"Rate limit exceeded. Please retry after {retry_after} seconds."
        else:
            message = "Rate limit exceeded. Please retry after a brief delay."

        super().__init__(
            status_code=429,
            message=message,
            original_error=original_error,
            details={'retry_after': retry_after}
        )
        self.retry_after = retry_after


class TransientError(AzureDevOpsError):
    """
    Raised for temporary service errors (HTTP 500, 502, 503, 504).

    These errors are typically transient and should be retried:
    - 500 Internal Server Error
    - 502 Bad Gateway
    - 503 Service Unavailable
    - 504 Gateway Timeout
    """

    def __init__(
        self,
        status_code: int,
        original_error: Optional[Exception] = None
    ):
        message = (
            f"Azure DevOps service temporarily unavailable (HTTP {status_code}). "
            "This error is transient and will be retried automatically."
        )

        super().__init__(
            status_code=status_code,
            message=message,
            original_error=original_error
        )


class BadRequestError(AzureDevOpsError):
    """
    Raised for malformed requests (HTTP 400).

    This can occur when:
    - Invalid field values
    - Invalid WIQL syntax
    - Missing required fields
    - Invalid work item type
    """

    def __init__(
        self,
        message: str = "Bad request. Please check your input values.",
        original_error: Optional[Exception] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            status_code=400,
            message=message,
            original_error=original_error,
            details=details
        )


class ConflictError(AzureDevOpsError):
    """
    Raised when there's a conflict with existing data (HTTP 409).

    This can occur when:
    - Work item has been modified since it was retrieved
    - Concurrent updates detected
    """

    def __init__(
        self,
        message: str = "Conflict detected. The resource has been modified by another user.",
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            status_code=409,
            message=message,
            original_error=original_error
        )


class TimeoutError(AzureDevOpsError):
    """
    Raised when a request times out.

    This can occur when:
    - Azure DevOps API is slow to respond
    - Network connectivity issues
    - Query is too complex
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
        original_error: Optional[Exception] = None
    ):
        message = (
            f"Request timeout after {timeout_seconds} seconds. "
            "Azure DevOps may be experiencing issues or the query is too complex."
        )

        super().__init__(
            status_code=408,
            message=message,
            original_error=original_error,
            details={'timeout_seconds': timeout_seconds}
        )


class QueryTooLargeError(AzureDevOpsError):
    """
    Raised when a query returns too many results.

    This can occur when:
    - Query doesn't have a TOP clause
    - Query matches thousands of work items
    - Need to add more specific filters
    """

    def __init__(
        self,
        result_count: Optional[int] = None,
        max_results: int = 20000,
        original_error: Optional[Exception] = None
    ):
        if result_count:
            message = (
                f"Query returned {result_count} results, exceeding maximum of {max_results}. "
                "Please add a TOP clause or more specific filters."
            )
        else:
            message = (
                f"Query result too large (max {max_results} items). "
                "Please add a TOP clause or more specific filters."
            )

        super().__init__(
            status_code=413,
            message=message,
            original_error=original_error,
            details={'result_count': result_count, 'max_results': max_results}
        )


def map_status_code_to_error(
    status_code: int,
    original_error: Optional[Exception] = None,
    **kwargs
) -> AzureDevOpsError:
    """
    Map HTTP status code to appropriate error class.

    Args:
        status_code: HTTP status code from Azure DevOps API
        original_error: The original exception
        **kwargs: Additional error-specific parameters

    Returns:
        Appropriate AzureDevOpsError subclass instance
    """
    if status_code == 400:
        return BadRequestError(original_error=original_error, **kwargs)
    elif status_code == 401:
        return AuthenticationError(original_error=original_error)
    elif status_code == 403:
        return PermissionDeniedError(original_error=original_error, **kwargs)
    elif status_code == 404:
        return WorkItemNotFoundError(original_error=original_error, **kwargs)
    elif status_code == 408:
        return TimeoutError(original_error=original_error, **kwargs)
    elif status_code == 409:
        return ConflictError(original_error=original_error)
    elif status_code == 413:
        return QueryTooLargeError(original_error=original_error, **kwargs)
    elif status_code == 429:
        return RateLimitError(original_error=original_error, **kwargs)
    elif status_code in [500, 502, 503, 504]:
        return TransientError(status_code=status_code, original_error=original_error)
    else:
        return AzureDevOpsError(
            status_code=status_code,
            message=f"Azure DevOps API error: HTTP {status_code}",
            original_error=original_error
        )
