"""
Unit tests for decorators module.

Tests retry logic, timeout handling, and error handling decorators.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from src.decorators import (
    retry_on_transient_error,
    with_timeout,
    azure_devops_operation
)
from src.errors import (
    TransientError,
    RateLimitError,
    WorkItemNotFoundError
)


class TestRetryDecorator:
    """Test retry_on_transient_error decorator."""

    @pytest.mark.asyncio
    async def test_retry_successful_first_attempt(self):
        """Test that successful calls don't retry."""
        call_count = 0

        @retry_on_transient_error(max_retries=3)
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_error_succeeds(self):
        """Test that transient errors are retried and eventually succeed."""
        call_count = 0

        @retry_on_transient_error(max_retries=3, base_delay=0.01)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError(status_code=503)
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test that retries are exhausted and error is raised."""
        call_count = 0

        @retry_on_transient_error(max_retries=2, base_delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise TransientError(status_code=503)

        with pytest.raises(TransientError):
            await always_fails()

        # Should be called 3 times: initial + 2 retries
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_non_transient_error_not_retried(self):
        """Test that non-transient errors are not retried."""
        call_count = 0

        @retry_on_transient_error(max_retries=3)
        async def non_transient_error():
            nonlocal call_count
            call_count += 1
            raise WorkItemNotFoundError(work_item_id=123)

        with pytest.raises(WorkItemNotFoundError):
            await non_transient_error()

        # Should only be called once (no retries for non-transient errors)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_rate_limit_with_retry_after(self):
        """Test that rate limits with retry-after are handled."""
        call_count = 0

        @retry_on_transient_error(max_retries=2, base_delay=0.01)
        async def rate_limited():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError(retry_after=0.05)  # 50ms
            return "success"

        start_time = time.time()
        result = await rate_limited()
        elapsed = time.time() - start_time

        assert result == "success"
        assert call_count == 2
        # Should have waited at least 50ms for retry_after
        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test exponential backoff between retries."""
        call_times = []

        @retry_on_transient_error(max_retries=3, base_delay=0.05, exponential_base=2.0)
        async def track_timing():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise TransientError(status_code=503)
            return "success"

        await track_timing()

        # Calculate delays between calls
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times) - 1)]

        # First delay: ~50ms, second delay: ~100ms (exponential)
        assert delays[0] >= 0.045  # Allow some margin
        assert delays[1] >= 0.090  # Should be roughly 2x first delay


class TestTimeoutDecorator:
    """Test with_timeout decorator."""

    @pytest.mark.asyncio
    async def test_timeout_successful_completion(self):
        """Test that fast functions complete successfully."""
        @with_timeout(timeout_seconds=1.0)
        async def fast_function():
            await asyncio.sleep(0.1)
            return "success"

        result = await fast_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_raises_error(self):
        """Test that slow functions timeout."""
        @with_timeout(timeout_seconds=0.1)
        async def slow_function():
            await asyncio.sleep(1.0)
            return "should not reach here"

        with pytest.raises(asyncio.TimeoutError):
            await slow_function()

    @pytest.mark.asyncio
    async def test_timeout_with_arguments(self):
        """Test that timeout works with function arguments."""
        @with_timeout(timeout_seconds=1.0)
        async def function_with_args(a, b, c=None):
            await asyncio.sleep(0.1)
            return f"{a}-{b}-{c}"

        result = await function_with_args("x", "y", c="z")
        assert result == "x-y-z"


class TestAzureDevOpsOperationDecorator:
    """Test azure_devops_operation unified decorator."""

    @pytest.mark.asyncio
    async def test_operation_successful(self):
        """Test successful operation."""
        @azure_devops_operation()
        async def successful_op():
            return "success"

        result = await successful_op()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_operation_with_timeout(self):
        """Test operation timeout."""
        @azure_devops_operation(timeout_seconds=0.1)
        async def slow_op():
            await asyncio.sleep(1.0)
            return "should not reach"

        with pytest.raises(asyncio.TimeoutError):
            await slow_op()

    @pytest.mark.asyncio
    async def test_operation_with_retry(self):
        """Test operation retry on transient errors."""
        call_count = 0

        @azure_devops_operation(max_retries=3)
        async def flaky_op():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TransientError(status_code=503)
            return "success"

        result = await flaky_op()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_operation_non_transient_error_not_retried(self):
        """Test that non-transient errors are not retried."""
        call_count = 0

        @azure_devops_operation(max_retries=3)
        async def non_transient_op():
            nonlocal call_count
            call_count += 1
            raise WorkItemNotFoundError(work_item_id=123)

        with pytest.raises(WorkItemNotFoundError):
            await non_transient_op()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_operation_with_arguments(self):
        """Test operation with function arguments."""
        @azure_devops_operation()
        async def op_with_args(a, b, c=None):
            return f"{a}+{b}+{c}"

        result = await op_with_args(1, 2, c=3)
        assert result == "1+2+3"

    @pytest.mark.asyncio
    async def test_operation_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @azure_devops_operation()
        async def my_operation():
            return "test"

        assert my_operation.__name__ == "my_operation"


class TestDecoratorCombinations:
    """Test combinations of decorators."""

    @pytest.mark.asyncio
    async def test_retry_with_timeout(self):
        """Test retry and timeout working together."""
        call_count = 0

        @with_timeout(timeout_seconds=1.0)
        @retry_on_transient_error(max_retries=2, base_delay=0.01)
        async def combined():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TransientError(status_code=503)
            await asyncio.sleep(0.1)
            return "success"

        result = await combined()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_multiple_retries_within_timeout(self):
        """Test that retries complete within timeout."""
        call_count = 0

        @with_timeout(timeout_seconds=0.5)
        @retry_on_transient_error(max_retries=5, base_delay=0.01)
        async def many_retries():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError(status_code=503)
            return "success"

        result = await many_retries()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_timeout_during_retry(self):
        """Test that timeout can occur during retries."""
        @with_timeout(timeout_seconds=0.1)
        @retry_on_transient_error(max_retries=10, base_delay=0.5)
        async def slow_retries():
            raise TransientError(status_code=503)

        # Should timeout before completing all retries
        with pytest.raises(asyncio.TimeoutError):
            await slow_retries()


class TestDecoratorErrorHandling:
    """Test error handling in decorators."""

    @pytest.mark.asyncio
    async def test_decorator_preserves_error_details(self):
        """Test that decorators preserve error details."""
        @azure_devops_operation()
        async def error_op():
            raise WorkItemNotFoundError(work_item_id=456)

        with pytest.raises(WorkItemNotFoundError) as exc_info:
            await error_op()

        error = exc_info.value
        assert "456" in str(error)
        assert error.status_code == 404

    @pytest.mark.asyncio
    async def test_decorator_with_rate_limit(self):
        """Test decorator handling rate limit errors."""
        call_count = 0

        @azure_devops_operation(max_retries=2)
        async def rate_limited_op():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError(retry_after=0.01)
            return "success"

        result = await rate_limited_op()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_decorator_with_generic_exception(self):
        """Test that decorators don't catch non-Azure DevOps errors."""
        @azure_devops_operation()
        async def generic_error():
            raise ValueError("Generic error")

        # Generic errors should pass through without retry
        with pytest.raises(ValueError):
            await generic_error()


class TestDecoratorPerformance:
    """Test decorator performance characteristics."""

    @pytest.mark.asyncio
    async def test_retry_delay_increases_exponentially(self):
        """Test that retry delays increase exponentially."""
        call_times = []

        @retry_on_transient_error(max_retries=4, base_delay=0.02, exponential_base=2.0)
        async def measure_delays():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise TransientError(status_code=503)
            return "success"

        await measure_delays()

        # Calculate delays
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times) - 1)]

        # Delays should be approximately: 20ms, 40ms, 80ms
        # Allow 50% margin for timing variability
        assert 0.015 <= delays[0] <= 0.030  # ~20ms
        assert 0.030 <= delays[1] <= 0.060  # ~40ms
        assert 0.060 <= delays[2] <= 0.120  # ~80ms

    @pytest.mark.asyncio
    async def test_no_delay_on_success(self):
        """Test that successful calls have no artificial delay."""
        @retry_on_transient_error(max_retries=3, base_delay=1.0)
        async def instant_success():
            return "success"

        start = time.time()
        await instant_success()
        elapsed = time.time() - start

        # Should complete instantly (< 100ms)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_timeout_precision(self):
        """Test that timeout is relatively precise."""
        @with_timeout(timeout_seconds=0.2)
        async def precise_timeout():
            await asyncio.sleep(1.0)

        start = time.time()
        with pytest.raises(asyncio.TimeoutError):
            await precise_timeout()
        elapsed = time.time() - start

        # Should timeout close to specified time (within 50ms)
        assert 0.18 <= elapsed <= 0.25


class TestDecoratorUsagePatterns:
    """Test common usage patterns."""

    @pytest.mark.asyncio
    async def test_decorator_on_class_method(self):
        """Test decorator on class methods."""
        class Service:
            def __init__(self):
                self.call_count = 0

            @azure_devops_operation()
            async def get_data(self, work_item_id):
                self.call_count += 1
                return f"data_{work_item_id}"

        service = Service()
        result = await service.get_data(123)

        assert result == "data_123"
        assert service.call_count == 1

    @pytest.mark.asyncio
    async def test_decorator_with_retries_on_method(self):
        """Test decorator with retries on class method."""
        class Service:
            def __init__(self):
                self.attempt = 0

            @azure_devops_operation(max_retries=3)
            async def flaky_method(self):
                self.attempt += 1
                if self.attempt < 2:
                    raise TransientError(status_code=503)
                return "success"

        service = Service()
        result = await service.flaky_method()

        assert result == "success"
        assert service.attempt == 2
