# core/throttling.py
"""
Request throttling to prevent API quota exhaustion on production
Implements sliding window rate limiting
"""

import time
import logging
from threading import Lock
from collections import deque
from functools import wraps
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window
    Prevents burst requests from hitting API quotas
    """
    
    def __init__(self, max_requests: int = 4, time_window: int = 60):
        """
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed within rate limit"""
        with self.lock:
            now = time.time()
            
            # Remove old requests outside time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Check if we can allow this request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                logger.info(f"[THROTTLE] Request allowed ({len(self.requests)}/{self.max_requests})")
                return True
            else:
                logger.warning(f"[THROTTLE] Rate limit exceeded ({len(self.requests)}/{self.max_requests})")
                return False
    
    def get_retry_after(self) -> float:
        """Get seconds to wait before next request allowed"""
        with self.lock:
            if self.requests:
                oldest = self.requests[0]
                retry_after = (oldest + self.time_window) - time.time()
                return max(0, retry_after)
            return 0


# Global rate limiter for pest detection (30 requests per 60 seconds = reasonable for production)
pest_detection_limiter = RateLimiter(max_requests=30, time_window=60)


def throttle_pest_detection(func):
    """
    Decorator to throttle pest detection requests
    Prevents hitting Gemini free tier quota on production
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not pest_detection_limiter.is_allowed():
            logger.warning("[THROTTLE] Pest detection rate limited, using fallback")
            # Return JSON response with fallback data (NOT a dict!)
            from core.services.pest_detection import RuleBasedPestDetector
            fallback_data = RuleBasedPestDetector.get_fallback_response("Rate limit - trying again soon")
            response = JsonResponse(
                fallback_data,
                status=429  # HTTP 429 Too Many Requests
            )
            response['Retry-After'] = '60'  # Suggest retry after 60 seconds
            return response
        
        return func(*args, **kwargs)
    
    return wrapper
