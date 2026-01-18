"""
Rate Limiting Module
Provides rate limiting functionality using slowapi with Redis backend support.
"""

from typing import Callable, Optional
from functools import wraps

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.utils.logging import logger


def get_client_identifier(request: Request) -> str:
    """
    Get unique client identifier for rate limiting.
    Uses X-Forwarded-For header if behind proxy, otherwise remote address.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address or identifier
    """
    # Check for forwarded header (when behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to remote address
    return get_remote_address(request)


def get_api_key_identifier(request: Request) -> str:
    """
    Get identifier based on API key if present.
    Falls back to IP address if no API key.
    
    Args:
        request: FastAPI request object
        
    Returns:
        API key or client IP
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key[:16]}"  # Use prefix of API key
    return get_client_identifier(request)


# Initialize rate limiter
# In production with Redis:
# limiter = Limiter(key_func=get_client_identifier, storage_uri=settings.redis_url)
# For development without Redis:
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Args:
        request: FastAPI request object
        exc: Rate limit exceeded exception
        
    Returns:
        JSON response with rate limit error
    """
    from fastapi.responses import JSONResponse
    from datetime import datetime
    
    logger.warning(
        "rate_limit_exceeded",
        client_ip=get_client_identifier(request),
        path=request.url.path,
        limit=str(exc.detail)
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded: {exc.detail}",
                "details": {
                    "retry_after": "60 seconds"
                }
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
            "X-RateLimit-Remaining": "0"
        }
    )


# Rate limiting decorators for different tiers
def rate_limit_standard(func: Callable) -> Callable:
    """
    Standard rate limit decorator (60/minute).
    Use for regular endpoints.
    """
    @wraps(func)
    @limiter.limit(f"{settings.rate_limit_per_minute}/minute")
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


def rate_limit_strict(func: Callable) -> Callable:
    """
    Strict rate limit decorator (10/minute).
    Use for expensive operations like predictions.
    """
    @wraps(func)
    @limiter.limit("10/minute")
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


def rate_limit_relaxed(func: Callable) -> Callable:
    """
    Relaxed rate limit decorator (120/minute).
    Use for lightweight endpoints like health checks.
    """
    @wraps(func)
    @limiter.limit("120/minute")
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


def rate_limit_burst(func: Callable) -> Callable:
    """
    Burst rate limit decorator (300/minute, 20/second).
    Use for high-frequency endpoints with burst protection.
    """
    @wraps(func)
    @limiter.limit("20/second;300/minute")
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


def rate_limit_custom(limit_string: str) -> Callable:
    """
    Custom rate limit decorator.
    
    Args:
        limit_string: Rate limit string (e.g., "100/hour", "5/minute")
        
    Returns:
        Decorator function
        
    Example:
        @rate_limit_custom("100/hour")
        async def my_endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @limiter.limit(limit_string)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimitMiddleware:
    """
    Middleware to add rate limit headers to responses.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                # Add rate limit headers
                headers[b"x-ratelimit-limit"] = str(settings.rate_limit_per_minute).encode()
                message["headers"] = list(headers.items())
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
