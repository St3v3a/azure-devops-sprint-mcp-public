"""
Decorators for error handling, retry logic, and request management.

Provides robust error handling and automatic retry for transient failures
in Azure DevOps API operations.
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar, Any, Optional

from .errors import (
    AzureDevOpsError,
    map_status_code_to_error,
    RateLimitError,
    TransientError,
    TimeoutError as ADOTimeoutError
)

# Type variable for generic function signatures
T = TypeVar('T')

# Configure logging
logger = logging.getLogger(__name__)


def handle_ado_error(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle Azure DevOps API errors with helpful messages.

    Maps Azure DevOps SDK exceptions to custom error classes with
    user-friendly messages.

    Args:
        func: The async function to wrap

    Returns:
        Wrapped function with error handling

    Example:
        @handle_ado_error
        async def get_work_item(self, work_item_id: int):
            return self.wit_client.get_work_item(id=work_item_id)
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AzureDevOpsError:
            # Already a custom error, re-raise as-is
            raise
        except Exception as e:
            # Try to extract status code from Azure DevOps SDK exception
            status_code = getattr(e, 'status_code', None)

            # If no status code, check response object
            if not status_code and hasattr(e, 'response'):
                response = getattr(e, 'response', None)
                if response:
                    status_code = getattr(response, 'status_code', None)

            if status_code:
                # Extract additional headers for rate limiting
                retry_after = None
                if status_code == 429:
                    # Try to extract Retry-After header
                    if hasattr(e, 'response') and e.response:
                        response = e.response
                        # Try to get headers from response
                        if hasattr(response, 'headers'):
                            headers = response.headers
                            # Retry-After can be in seconds or HTTP-date
                            retry_after_header = headers.get('Retry-After') or headers.get('retry-after')
                            if retry_after_header:
                                try:
                                    # Try to parse as integer (seconds)
                                    retry_after = int(retry_after_header)
                                except (ValueError, TypeError):
                                    # If not an integer, might be HTTP-date format
                                    # Default to 60 seconds if we can't parse
                                    retry_after = 60
                                    logger.warning(f"Could not parse Retry-After header: {retry_after_header}")

                # Map to custom error with rate limit info
                error = map_status_code_to_error(
                    status_code,
                    original_error=e,
                    retry_after=retry_after if retry_after else None
                )
                logger.error(
                    f"Azure DevOps API error in {func.__name__}: {error}",
                    exc_info=True
                )
                raise error
            else:
                # Unknown error
                logger.error(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise AzureDevOpsError(
                    message=f"Unexpected error in {func.__name__}: {str(e)}",
                    original_error=e
                )

    return wrapper


def retry_on_transient_error(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry operations on transient errors with exponential backoff.

    Automatically retries on:
    - Rate limit errors (429)
    - Server errors (500, 502, 503, 504)

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        max_delay: Maximum delay between retries (default: 60.0)

    Returns:
        Decorator function

    Example:
        @retry_on_transient_error(max_retries=3, base_delay=1.0)
        @handle_ado_error
        async def get_work_item(self, work_item_id: int):
            return self.wit_client.get_work_item(id=work_item_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (RateLimitError, TransientError) as e:
                    last_error = e

                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        raise

                    # Calculate delay
                    if isinstance(e, RateLimitError) and e.retry_after:
                        # Respect Retry-After header
                        delay = min(e.retry_after, max_delay)
                    else:
                        # Exponential backoff
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )

                    logger.warning(
                        f"Transient error in {func.__name__} (attempt {attempt + 1}/{max_retries}): "
                        f"{e}. Retrying in {delay:.1f}s..."
                    )

                    await asyncio.sleep(delay)
                except AzureDevOpsError:
                    # Non-transient error, don't retry
                    raise
                except Exception:
                    # Unknown error, don't retry
                    raise

            # Should never reach here, but raise last error if we do
            if last_error:
                raise last_error

        return wrapper
    return decorator


def with_timeout(timeout_seconds: int = 30) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add timeout to async operations.

    Args:
        timeout_seconds: Timeout in seconds (default: 30)

    Returns:
        Decorator function

    Example:
        @with_timeout(timeout_seconds=30)
        @retry_on_transient_error()
        @handle_ado_error
        async def get_work_item(self, work_item_id: int):
            return self.wit_client.get_work_item(id=work_item_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError as e:
                logger.error(
                    f"Timeout after {timeout_seconds}s in {func.__name__}"
                )
                raise ADOTimeoutError(
                    timeout_seconds=timeout_seconds,
                    original_error=e
                )

        return wrapper
    return decorator


def log_execution(
    level: int = logging.INFO,
    log_args: bool = False,
    log_result: bool = False
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to log function execution.

    Args:
        level: Logging level (default: INFO)
        log_args: Whether to log function arguments (default: False)
        log_result: Whether to log function result (default: False)

    Returns:
        Decorator function

    Example:
        @log_execution(level=logging.DEBUG, log_args=True)
        async def get_work_item(self, work_item_id: int):
            return self.wit_client.get_work_item(id=work_item_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__

            # Log entry
            if log_args:
                logger.log(
                    level,
                    f"Calling {func_name} with args={args}, kwargs={kwargs}"
                )
            else:
                logger.log(level, f"Calling {func_name}")

            # Execute function
            try:
                result = await func(*args, **kwargs)

                # Log success
                if log_result:
                    logger.log(level, f"{func_name} completed with result: {result}")
                else:
                    logger.log(level, f"{func_name} completed successfully")

                return result
            except Exception as e:
                logger.log(level, f"{func_name} failed with error: {e}")
                raise

        return wrapper
    return decorator


def validate_work_item_id(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to validate work item ID parameter.

    Ensures work_item_id is a positive integer.

    Args:
        func: The async function to wrap

    Returns:
        Wrapped function with validation

    Example:
        @validate_work_item_id
        async def get_work_item(self, work_item_id: int):
            return self.wit_client.get_work_item(id=work_item_id)
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if work_item_id is in kwargs
        work_item_id = kwargs.get('work_item_id')

        # If not in kwargs, check positional args
        # Assuming work_item_id is typically the first or second parameter
        if work_item_id is None and len(args) > 1:
            # First arg is usually 'self', second might be work_item_id
            potential_id = args[1]
            if isinstance(potential_id, int):
                work_item_id = potential_id

        if work_item_id is not None:
            if not isinstance(work_item_id, int) or work_item_id <= 0:
                from .errors import BadRequestError
                raise BadRequestError(
                    message=f"Invalid work item ID: {work_item_id}. Must be a positive integer."
                )

        return await func(*args, **kwargs)

    return wrapper


# Convenience decorator that combines common decorators
def azure_devops_operation(
    timeout_seconds: int = 30,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Convenience decorator combining timeout, retry, and error handling.

    Applies decorators in the correct order:
    1. Timeout wrapper (outermost)
    2. Retry on transient errors
    3. Error handling (innermost)

    Args:
        timeout_seconds: Request timeout in seconds (default: 30)
        max_retries: Maximum retry attempts (default: 3)
        base_delay: Initial retry delay in seconds (default: 1.0)

    Returns:
        Decorator function

    Example:
        @azure_devops_operation(timeout_seconds=60, max_retries=5)
        async def get_work_item(self, work_item_id: int):
            return self.wit_client.get_work_item(id=work_item_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply decorators in reverse order (bottom to top)
        decorated = func
        decorated = handle_ado_error(decorated)
        decorated = retry_on_transient_error(
            max_retries=max_retries,
            base_delay=base_delay
        )(decorated)
        decorated = with_timeout(timeout_seconds)(decorated)
        return decorated

    return decorator


# Performance monitoring decorator
class PerformanceMonitor:
    """
    Context manager and decorator for monitoring operation performance.

    Tracks execution time and logs slow operations.
    """

    def __init__(self, operation_name: str, warn_threshold_ms: float = 1000.0):
        """
        Initialize performance monitor.

        Args:
            operation_name: Name of the operation being monitored
            warn_threshold_ms: Threshold in milliseconds to log warnings (default: 1000)
        """
        self.operation_name = operation_name
        self.warn_threshold_ms = warn_threshold_ms
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    async def __aenter__(self):
        """Start monitoring."""
        self.start_time = asyncio.get_event_loop().time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End monitoring and log results."""
        self.end_time = asyncio.get_event_loop().time()
        duration_ms = (self.end_time - self.start_time) * 1000

        if duration_ms > self.warn_threshold_ms:
            logger.warning(
                f"Slow operation: {self.operation_name} took {duration_ms:.1f}ms "
                f"(threshold: {self.warn_threshold_ms:.1f}ms)"
            )
        else:
            logger.debug(
                f"Operation {self.operation_name} completed in {duration_ms:.1f}ms"
            )

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Use as a decorator."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with PerformanceMonitor(
                operation_name=func.__name__,
                warn_threshold_ms=self.warn_threshold_ms
            ):
                return await func(*args, **kwargs)
        return wrapper
