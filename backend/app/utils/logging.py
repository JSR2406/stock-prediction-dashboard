"""
Structured Logging Module
Provides JSON-formatted logging with timestamps and request context.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import structlog
from functools import lru_cache

from app.config import settings


def add_timestamp(
    logger: logging.Logger, 
    method_name: str, 
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add ISO timestamp to log events."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_app_context(
    logger: logging.Logger, 
    method_name: str, 
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add application context to log events."""
    event_dict["app_name"] = settings.app_name
    event_dict["environment"] = settings.environment
    event_dict["version"] = settings.app_version
    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging for the application.
    Sets up both structlog and standard library logging.
    """
    # Determine log level
    log_level = getattr(logging, settings.log_level, logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Shared processors for both dev and prod
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_timestamp,
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json" or settings.is_production:
        # Production: JSON format
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: Console format with colors
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@lru_cache()
def get_logger(name: str = "app") -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (default: "app")
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class RequestLogger:
    """
    Context manager for logging request lifecycle.
    Provides structured logging for API requests.
    """
    
    def __init__(
        self,
        request_id: str,
        method: str,
        path: str,
        client_ip: Optional[str] = None
    ):
        self.logger = get_logger("request")
        self.request_id = request_id
        self.method = method
        self.path = path
        self.client_ip = client_ip
        self.start_time: Optional[datetime] = None
    
    def __enter__(self) -> "RequestLogger":
        """Log request start."""
        self.start_time = datetime.utcnow()
        self.logger.info(
            "request_started",
            request_id=self.request_id,
            method=self.method,
            path=self.path,
            client_ip=self.client_ip
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Log request completion."""
        duration_ms = None
        if self.start_time:
            duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type:
            self.logger.error(
                "request_failed",
                request_id=self.request_id,
                method=self.method,
                path=self.path,
                duration_ms=duration_ms,
                error_type=exc_type.__name__ if exc_type else None,
                error_message=str(exc_val) if exc_val else None
            )
        else:
            self.logger.info(
                "request_completed",
                request_id=self.request_id,
                method=self.method,
                path=self.path,
                duration_ms=duration_ms
            )
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log info message with request context."""
        self.logger.info(message, request_id=self.request_id, **kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message with request context."""
        self.logger.warning(message, request_id=self.request_id, **kwargs)
    
    def log_error(self, message: str, **kwargs) -> None:
        """Log error message with request context."""
        self.logger.error(message, request_id=self.request_id, **kwargs)


# Initialize logging on module load
configure_logging()

# Export default logger
logger = get_logger()
