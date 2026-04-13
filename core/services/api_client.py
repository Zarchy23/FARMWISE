# core/services/api_client.py
# Render-specific API client with retry logic and proper error handling
# Handles network issues common to Render free tier

import httpx
import logging
import time
from typing import Optional, Dict, Any, Callable
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

logger = logging.getLogger(__name__)

class RenderAPIClient:
    """
    HTTP client optimized for Render free tier
    - Automatic retries for transient failures
    - Exponential backoff for rate limits
    - Timeout handling
    - Connection pooling
    """
    
    def __init__(self, timeout=30.0, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(timeout=self.timeout)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request with retry logic"""
        logger.info(f"APIClient GET {url}")
        try:
            response = self.client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException:
            logger.warning(f"Timeout on GET {url}, retrying...")
            raise
        except httpx.ConnectError as e:
            logger.warning(f"Connection error on GET {url}: {e}, retrying...")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.status_code} on GET {url}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    def post(self, url: str, **kwargs) -> httpx.Response:
        """POST request with retry logic"""
        logger.info(f"APIClient POST {url}")
        try:
            response = self.client.post(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException:
            logger.warning(f"Timeout on POST {url}, retrying...")
            raise
        except httpx.ConnectError as e:
            logger.warning(f"Connection error on POST {url}: {e}, retrying...")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.status_code} on POST {url}")
            raise
    
    def close(self):
        """Close client connection"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class APICallWrapper:
    """
    Decorator/wrapper for wrapping API calls with retry logic
    Usage:
        wrapper = APICallWrapper(max_retries=3)
        result = wrapper.call(some_api_function, arg1, kwarg=value)
    """
    
    def __init__(self, max_retries=3, base_delay=2, max_delay=30):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call a function with automatic retry logic
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries exhausted
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"API call attempt {attempt}/{self.max_retries}: {func.__name__}")
                return func(*args, **kwargs)
                
            except (httpx.TimeoutException, httpx.ConnectError, ConnectionError) as e:
                last_error = e
                if attempt == self.max_retries:
                    logger.error(f"API call failed after {self.max_retries} attempts: {type(e).__name__}")
                    raise
                
                wait_time = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
                logger.warning(f"API call failed ({type(e).__name__}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                
            except Exception as e:
                # Non-transient errors, don't retry
                logger.error(f"Non-transient API error: {type(e).__name__}: {e}")
                raise
        
        # Should not reach here
        raise last_error or Exception("API call failed")


# Singleton instance
api_client = RenderAPIClient()
api_wrapper = APICallWrapper(max_retries=3)
