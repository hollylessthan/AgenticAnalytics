"""Retry utilities for agent execution with exponential backoff."""

import time
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 2,
    initial_delay_ms: int = 500,
    backoff_multiplier: float = 2.0,
    max_delay_ms: int = 10000,
    on_retry: Callable[[int, Exception], None] = None
) -> Callable:
    """Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 2)
        initial_delay_ms: Initial delay between retries in milliseconds (default: 500)
        backoff_multiplier: Multiplier for delay between retries (default: 2.0)
        max_delay_ms: Maximum delay between retries in milliseconds (default: 10000)
        on_retry: Optional callback function(attempt: int, error: Exception) called on each retry
        
    Returns:
        Decorator function
        
    Example:
        @retry_with_backoff(max_retries=2, initial_delay_ms=500)
        def my_function():
            # Function that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay_ms = initial_delay_ms
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate exponential backoff
                        delay_ms = min(delay_ms * backoff_multiplier, max_delay_ms)
                        delay_seconds = delay_ms / 1000.0
                        
                        # Call retry callback if provided
                        if on_retry:
                            on_retry(attempt + 1, e)
                        
                        logger.debug(
                            f"[Retry {attempt + 1}/{max_retries}] {func.__name__} failed with "
                            f"{type(e).__name__}: {str(e)}. Retrying in {delay_seconds:.1f}s..."
                        )
                        
                        time.sleep(delay_seconds)
                    else:
                        # All retries exhausted
                        logger.error(
                            f"[Final Attempt {attempt + 1}/{max_retries + 1}] {func.__name__} failed "
                            f"after {max_retries} retries: {type(e).__name__}: {str(e)}"
                        )
            
            # If we got here, all retries failed
            raise last_exception
        
        return wrapper
    
    return decorator


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(self, max_retries: int = 2, initial_delay_ms: int = 500):
        """Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retries
            initial_delay_ms: Initial delay between retries in milliseconds
        """
        self.max_retries = max_retries
        self.initial_delay_ms = initial_delay_ms
    
    @staticmethod
    def from_config(config) -> "RetryConfig":
        """Create RetryConfig from application config.
        
        Args:
            config: Application Config object
            
        Returns:
            RetryConfig instance
        """
        return RetryConfig(
            max_retries=config.agent_retry_count,
            initial_delay_ms=config.agent_retry_delay_ms
        )
