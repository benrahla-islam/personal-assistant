"""
Rate limiter to prevent API quota exhaustion
"""

import time
from datetime import datetime, timedelta
from typing import Optional
from config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Simple rate limiter that enforces a minimum time between requests.
    Helps prevent quota exhaustion and respects API rate limits.
    """
    
    def __init__(self, min_delay_seconds: float = 2.0, max_requests_per_minute: int = 15):
        """
        Initialize rate limiter.
        
        Args:
            min_delay_seconds: Minimum seconds between requests (default: 2.0)
            max_requests_per_minute: Maximum requests allowed per minute (default: 15)
        """
        self.min_delay = min_delay_seconds
        self.max_requests_per_minute = max_requests_per_minute
        self.last_request_time: Optional[float] = None
        self.request_timestamps = []
        
        logger.info(f"Rate limiter initialized: {min_delay_seconds}s delay, max {max_requests_per_minute} requests/min")
    
    def wait_if_needed(self):
        """
        Wait if necessary to respect rate limits.
        Call this before making an API request.
        """
        current_time = time.time()
        
        # Clean up old timestamps (older than 1 minute)
        one_minute_ago = current_time - 60
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > one_minute_ago]
        
        # Check if we're at the per-minute limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            # Calculate how long to wait until oldest request is > 1 minute old
            oldest_timestamp = self.request_timestamps[0]
            wait_time = 60 - (current_time - oldest_timestamp) + 0.1  # Add 0.1s buffer
            
            if wait_time > 0:
                logger.warning(f"⏳ Rate limit approaching: waiting {wait_time:.1f}s (requests per minute limit)")
                time.sleep(wait_time)
                current_time = time.time()
        
        # Check minimum delay between requests
        if self.last_request_time is not None:
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_delay:
                wait_time = self.min_delay - time_since_last
                logger.debug(f"⏳ Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                current_time = time.time()
        
        # Record this request
        self.last_request_time = current_time
        self.request_timestamps.append(current_time)
        
        # Log rate limit status
        requests_in_last_minute = len(self.request_timestamps)
        logger.debug(f"📊 Rate limit status: {requests_in_last_minute}/{self.max_requests_per_minute} requests in last minute")
    
    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        current_time = time.time()
        one_minute_ago = current_time - 60
        recent_requests = [ts for ts in self.request_timestamps if ts > one_minute_ago]
        
        return {
            "requests_last_minute": len(recent_requests),
            "max_requests_per_minute": self.max_requests_per_minute,
            "min_delay_seconds": self.min_delay,
            "time_since_last_request": current_time - self.last_request_time if self.last_request_time else None
        }


# Global rate limiter instance
# Adjust these values based on your Gemini API quota:
# Free tier: 15 requests per minute (RPM)
# Set min_delay to 4 seconds = 15 requests/minute max
_global_rate_limiter = RateLimiter(
    min_delay_seconds=4.0,  # 4 seconds between requests = max 15/minute
    max_requests_per_minute=15  # Gemini free tier limit
)


def wait_for_rate_limit():
    """
    Global function to enforce rate limiting before API calls.
    Use this before any Gemini API request.
    """
    _global_rate_limiter.wait_if_needed()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _global_rate_limiter


def configure_rate_limiter(min_delay_seconds: float = 4.0, max_requests_per_minute: int = 15):
    """
    Configure the global rate limiter settings.
    
    Args:
        min_delay_seconds: Minimum seconds between requests
        max_requests_per_minute: Maximum requests allowed per minute
    """
    global _global_rate_limiter
    _global_rate_limiter = RateLimiter(min_delay_seconds, max_requests_per_minute)
    logger.info(f"Rate limiter reconfigured: {min_delay_seconds}s delay, {max_requests_per_minute} RPM")
