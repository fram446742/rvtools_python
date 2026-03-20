"""Exponential backoff retry decorator for robust vCenter API calls"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Type, Tuple

logger = logging.getLogger("rvtools")


class RetryError(Exception):
    """Raised when max retries exceeded"""
    pass


def retry_with_backoff(
    retries: int = 3,
    initial_delay: float = 1,
    backoff_factor: float = 2,
    max_delay: float = 60,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1)
        backoff_factor: Backoff multiplier (default: 2 for exponential)
        max_delay: Maximum delay between retries (default: 60)
        exceptions: Tuple of exception types to catch (default: all)

    Example:
        @retry_with_backoff(retries=3, initial_delay=1, backoff_factor=2)
        def connect_to_vcenter():
            return service_instance.RetrieveContent()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(retries + 1):
                try:
                    logger.debug(f"Calling {func.__name__} (attempt {attempt + 1}/{retries + 1})")
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        logger.error(
                            f"{func.__name__} failed after {retries + 1} attempts: {e}",
                            exc_info=True
                        )
                        raise RetryError(f"Max retries ({retries + 1}) exceeded") from e

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

        return wrapper
    return decorator
