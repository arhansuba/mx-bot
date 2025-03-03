import time
import logging
import functools
import random
from typing import Callable, Any, Optional, Type, List, Tuple

logger = logging.getLogger(__name__)

def retry(
    max_tries: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Retry decorator with exponential backoff
    
    Args:
        max_tries (int): Maximum number of attempts
        delay_seconds (float): Initial delay between retries in seconds
        backoff_factor (float): Backoff multiplier
        jitter (bool): Whether to add random jitter to delay
        exceptions (tuple): Exception types to catch and retry
        
    Returns:
        Callable: Decorated function with retry logic
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_tries, delay_seconds
            
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    msg = f"{str(e)}, retrying in {mdelay} seconds..."
                    logger.warning(msg)
                    
                    # Add jitter to avoid thundering herd
                    if jitter:
                        jitter_range = mdelay * 0.2  # 20% jitter
                        mdelay = mdelay + random.uniform(-jitter_range, jitter_range)
                    
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff_factor
            
            # Last attempt
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

class RetryManager:
    """Utility class for managing retries with different strategies"""
    
    @staticmethod
    def with_exponential_backoff(
        func: Callable,
        *args,
        max_tries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        Call a function with exponential backoff retry logic
        
        Args:
            func (Callable): Function to call
            *args: Arguments to pass to the function
            max_tries (int): Maximum number of attempts
            initial_delay (float): Initial delay between retries in seconds
            backoff_factor (float): Backoff multiplier
            jitter (bool): Whether to add random jitter to delay
            exceptions (tuple): Exception types to catch and retry
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Any: Result of the function call
        """
        tries, delay = max_tries, initial_delay
        
        while tries > 1:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.warning(f"{str(e)}, retrying in {delay:.2f} seconds...")
                
                # Add jitter to avoid thundering herd
                if jitter:
                    jitter_range = delay * 0.2  # 20% jitter
                    sleep_time = delay + random.uniform(-jitter_range, jitter_range)
                else:
                    sleep_time = delay
                
                time.sleep(sleep_time)
                tries -= 1
                delay *= backoff_factor
        
        # Last attempt
        return func(*args, **kwargs)
    
    @staticmethod
    def with_custom_strategy(
        func: Callable,
        *args,
        max_tries: int = 3,
        delay_strategy: Callable[[int], float] = lambda attempt: 1.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        Call a function with custom retry strategy
        
        Args:
            func (Callable): Function to call
            *args: Arguments to pass to the function
            max_tries (int): Maximum number of attempts
            delay_strategy (Callable): Function that takes attempt number and returns delay
            exceptions (tuple): Exception types to catch and retry
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Any: Result of the function call
        """
        attempt = 1
        
        while attempt < max_tries:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                delay = delay_strategy(attempt)
                logger.warning(f"{str(e)}, retrying in {delay:.2f} seconds (attempt {attempt}/{max_tries})...")
                time.sleep(delay)
                attempt += 1
        
        # Last attempt
        return func(*args, **kwargs)

# Example usage:
# @retry(max_tries=5, delay_seconds=2, exceptions=(requests.RequestException,))
# def fetch_data(url):
#     return requests.get(url).json()