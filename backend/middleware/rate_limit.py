"""
Rate limiting middleware to prevent API abuse and quota exhaustion.

This module provides rate limiting at two levels:
1. Per-IP rate limiting to prevent individual client abuse
2. Global rate limiting to stay within Gemini API quotas
"""

import logging
import time
from collections import defaultdict
from typing import Dict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests per IP and globally.
    
    This middleware tracks request counts in sliding time windows and
    returns 429 Too Many Requests when limits are exceeded.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        global_requests_per_minute: int = 750,
        window_size: int = 100
    ):
        """Initialize rate limiter with configurable limits.
        
        Args:
            app: FastAPI application instance
            requests_per_minute: Max requests per IP per minute (default: 60)
            global_requests_per_minute: Max total requests per minute (default: 500)
            window_size: Time window in seconds (default: 60)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.global_requests_per_minute = global_requests_per_minute
        self.window_size = window_size
        
        # Track requests per IP: {ip: [timestamp, ...]}
        self._ip_requests: Dict[str, list] = defaultdict(list)
        
        # Track global requests: [timestamp, ...]
        self._global_requests: list = []
        
        # Last cleanup time
        self._last_cleanup = time.time()
        
        logger.info(
            f"Rate limiter initialized: {requests_per_minute} req/min per IP, "
            f"{global_requests_per_minute} req/min global"
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
        
        Returns:
            Response or 429 error if rate limit exceeded
        """
        # Skip rate limiting for health check endpoint
        if request.url.path == "/api/v1/health":
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Cleanup old entries periodically (every 60 seconds)
        if current_time - self._last_cleanup > 60:
            self._cleanup_old_entries(current_time)
            self._last_cleanup = current_time
        
        # Check global rate limit
        if not self._check_global_limit(current_time):
            logger.warning(f"Global rate limit exceeded")
            return self._rate_limit_response(
                "Global rate limit exceeded. Please try again later.",
                retry_after=self._calculate_retry_after(self._global_requests, current_time)
            )
        
        # Check per-IP rate limit
        if not self._check_ip_limit(client_ip, current_time):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return self._rate_limit_response(
                "Rate limit exceeded. Please slow down your requests.",
                retry_after=self._calculate_retry_after(self._ip_requests[client_ip], current_time)
            )
        
        # Record the request
        self._record_request(client_ip, current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = self._get_remaining_requests(client_ip, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers or connection.
        
        Args:
            request: HTTP request
        
        Returns:
            Client IP address
        """
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def _check_global_limit(self, current_time: float) -> bool:
        """Check if global rate limit is exceeded.
        
        Args:
            current_time: Current timestamp
        
        Returns:
            True if within limit, False if exceeded
        """
        # Remove expired entries
        cutoff_time = current_time - self.window_size
        self._global_requests = [
            timestamp for timestamp in self._global_requests
            if timestamp > cutoff_time
        ]
        
        # Check if limit exceeded
        return len(self._global_requests) < self.global_requests_per_minute
    
    def _check_ip_limit(self, client_ip: str, current_time: float) -> bool:
        """Check if per-IP rate limit is exceeded.
        
        Args:
            client_ip: Client IP address
            current_time: Current timestamp
        
        Returns:
            True if within limit, False if exceeded
        """
        # Remove expired entries for this IP
        cutoff_time = current_time - self.window_size
        self._ip_requests[client_ip] = [
            timestamp for timestamp in self._ip_requests[client_ip]
            if timestamp > cutoff_time
        ]
        
        # Check if limit exceeded
        return len(self._ip_requests[client_ip]) < self.requests_per_minute
    
    def _record_request(self, client_ip: str, current_time: float):
        """Record a request for rate limiting tracking.
        
        Args:
            client_ip: Client IP address
            current_time: Current timestamp
        """
        self._ip_requests[client_ip].append(current_time)
        self._global_requests.append(current_time)
    
    def _get_remaining_requests(self, client_ip: str, current_time: float) -> int:
        """Calculate remaining requests for an IP in current window.
        
        Args:
            client_ip: Client IP address
            current_time: Current timestamp
        
        Returns:
            Number of remaining requests
        """
        cutoff_time = current_time - self.window_size
        recent_requests = [
            timestamp for timestamp in self._ip_requests[client_ip]
            if timestamp > cutoff_time
        ]
        return max(0, self.requests_per_minute - len(recent_requests))
    
    def _calculate_retry_after(self, request_list: list, current_time: float) -> int:
        """Calculate seconds until rate limit resets.
        
        Args:
            request_list: List of request timestamps
            current_time: Current timestamp
        
        Returns:
            Seconds until oldest request expires from window
        """
        if not request_list:
            return self.window_size
        
        cutoff_time = current_time - self.window_size
        recent_requests = [ts for ts in request_list if ts > cutoff_time]
        
        if not recent_requests:
            return 1
        
        oldest_request = min(recent_requests)
        retry_after = int(oldest_request + self.window_size - current_time) + 1
        return max(1, retry_after)
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove expired entries to prevent memory growth.
        
        Args:
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.window_size
        
        # Clean global requests
        self._global_requests = [
            timestamp for timestamp in self._global_requests
            if timestamp > cutoff_time
        ]
        
        # Clean per-IP requests
        ips_to_remove = []
        for ip, timestamps in self._ip_requests.items():
            self._ip_requests[ip] = [
                timestamp for timestamp in timestamps
                if timestamp > cutoff_time
            ]
            # Remove IPs with no recent requests
            if not self._ip_requests[ip]:
                ips_to_remove.append(ip)
        
        for ip in ips_to_remove:
            del self._ip_requests[ip]
        
        logger.debug(
            f"Cleanup complete: {len(self._ip_requests)} active IPs, "
            f"{len(self._global_requests)} global requests in window"
        )
    
    def _rate_limit_response(self, message: str, retry_after: int) -> JSONResponse:
        """Create a 429 rate limit error response.
        
        Args:
            message: Error message
            retry_after: Seconds until retry
        
        Returns:
            JSONResponse with 429 status
        """
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": {
                    "code": 429,
                    "message": message
                }
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + retry_after))
            }
        )
