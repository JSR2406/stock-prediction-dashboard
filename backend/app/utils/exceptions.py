"""
Custom Exception Classes and Error Handling
Provides standardized exception handling across the application.
"""

from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """
    Base exception class for all API exceptions.
    Provides consistent error structure for API responses.
    """
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.field = field
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        error_dict = {
            "code": self.code,
            "message": self.message
        }
        if self.field:
            error_dict["field"] = self.field
        if self.details:
            error_dict["details"] = self.details
        return error_dict


# ============== 400 Bad Request Errors ==============

class BadRequestException(BaseAPIException):
    """Exception for malformed or invalid requests."""
    
    def __init__(
        self,
        message: str = "Bad request",
        code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details,
            field=field
        )


class ValidationException(BaseAPIException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details,
            field=field
        )


class InvalidSymbolException(BaseAPIException):
    """Exception for invalid stock/crypto symbols."""
    
    def __init__(self, symbol: str, market: str = "unknown"):
        super().__init__(
            message=f"Invalid symbol '{symbol}' for market '{market}'",
            code="INVALID_SYMBOL",
            status_code=400,
            details={"symbol": symbol, "market": market},
            field="symbol"
        )


# ============== 401 Unauthorized Errors ==============

class UnauthorizedException(BaseAPIException):
    """Exception for authentication failures."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details
        )


class InvalidAPIKeyException(BaseAPIException):
    """Exception for invalid API key."""
    
    def __init__(self, service: str = "API"):
        super().__init__(
            message=f"Invalid or missing {service} API key",
            code="INVALID_API_KEY",
            status_code=401,
            details={"service": service}
        )


# ============== 403 Forbidden Errors ==============

class ForbiddenException(BaseAPIException):
    """Exception for forbidden access."""
    
    def __init__(
        self,
        message: str = "Access forbidden",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details
        )


# ============== 404 Not Found Errors ==============

class NotFoundException(BaseAPIException):
    """Exception for resource not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details if details else None
        )


class StockNotFoundException(NotFoundException):
    """Exception for stock not found."""
    
    def __init__(self, symbol: str, exchange: str = "unknown"):
        super().__init__(
            message=f"Stock '{symbol}' not found on exchange '{exchange}'",
            resource_type="stock",
            resource_id=symbol
        )
        self.details["exchange"] = exchange


class CryptoNotFoundException(NotFoundException):
    """Exception for cryptocurrency not found."""
    
    def __init__(self, symbol: str):
        super().__init__(
            message=f"Cryptocurrency '{symbol}' not found",
            resource_type="cryptocurrency",
            resource_id=symbol
        )


class ModelNotFoundException(NotFoundException):
    """Exception for ML model not found."""
    
    def __init__(self, model_name: str):
        super().__init__(
            message=f"ML model '{model_name}' not found or not loaded",
            resource_type="ml_model",
            resource_id=model_name
        )


# ============== 429 Rate Limit Errors ==============

class RateLimitExceededException(BaseAPIException):
    """Exception for rate limit exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details if details else None
        )


# ============== 500 Internal Server Errors ==============

class InternalServerException(BaseAPIException):
    """Exception for internal server errors."""
    
    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="INTERNAL_ERROR",
            status_code=500,
            details=details
        )


class DatabaseException(BaseAPIException):
    """Exception for database errors."""
    
    def __init__(
        self,
        message: str = "Database error occurred",
        operation: Optional[str] = None
    ):
        details = {"operation": operation} if operation else None
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details
        )


class CacheException(BaseAPIException):
    """Exception for cache (Redis) errors."""
    
    def __init__(
        self,
        message: str = "Cache error occurred",
        operation: Optional[str] = None
    ):
        details = {"operation": operation} if operation else None
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            status_code=500,
            details=details
        )


class MLModelException(BaseAPIException):
    """Exception for ML model errors."""
    
    def __init__(
        self,
        message: str = "ML model error occurred",
        model_name: Optional[str] = None,
        operation: Optional[str] = None
    ):
        details = {}
        if model_name:
            details["model_name"] = model_name
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            code="ML_MODEL_ERROR",
            status_code=500,
            details=details if details else None
        )


# ============== 502/503 External Service Errors ==============

class ExternalServiceException(BaseAPIException):
    """Exception for external service failures."""
    
    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        status_code: int = 502
    ):
        super().__init__(
            message=f"{service_name}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status_code,
            details={"service": service_name}
        )


class YahooFinanceException(ExternalServiceException):
    """Exception for Yahoo Finance API errors."""
    
    def __init__(self, message: str = "Failed to fetch data from Yahoo Finance"):
        super().__init__(
            service_name="Yahoo Finance",
            message=message,
            status_code=502
        )


class CoinGeckoException(ExternalServiceException):
    """Exception for CoinGecko API errors."""
    
    def __init__(self, message: str = "Failed to fetch data from CoinGecko"):
        super().__init__(
            service_name="CoinGecko",
            message=message,
            status_code=502
        )


class MetalsAPIException(ExternalServiceException):
    """Exception for Metals API errors."""
    
    def __init__(self, message: str = "Failed to fetch data from Metals API"):
        super().__init__(
            service_name="Metals API",
            message=message,
            status_code=502
        )


class ServiceUnavailableException(BaseAPIException):
    """Exception for service unavailable."""
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details=details if details else None
        )
