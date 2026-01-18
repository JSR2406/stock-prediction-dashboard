"""
Stock Prediction Dashboard - FastAPI Main Application
Production-ready API with comprehensive error handling, rate limiting, and structured logging.
"""

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.utils.logging import logger, RequestLogger
from app.utils.cache import cache_manager
from app.utils.rate_limiter import limiter, rate_limit_handler
from app.utils.exceptions import BaseAPIException
from app.routes import stocks, crypto, commodities, predictions, analysis, websocket, history
from app.models.schemas import HealthCheckResponse, ServiceHealth, ErrorResponse, ErrorDetail


# Application startup time for uptime calculation
APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("application_starting", version=settings.app_version, environment=settings.environment)
    await cache_manager.initialize()
    logger.info("application_started")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered stock market prediction dashboard API for Indian markets (NSE/BSE), crypto, and commodities",
    version=settings.app_version,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)


# ============== Middleware ==============

@app.middleware("http")
async def request_middleware(request: Request, call_next: Callable) -> Response:
    """Add request ID, timing, and logging to all requests."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Add request ID to state
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None
    )
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error("request_error", request_id=request_id, error=str(e))
        raise
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    
    # Log response
    logger.info(
        "request_completed",
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2)
    )
    
    return response


# ============== Exception Handlers ==============

@app.exception_handler(BaseAPIException)
async def custom_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Handle custom API exceptions."""
    logger.warning(
        "api_exception",
        request_id=getattr(request.state, "request_id", None),
        error_code=exc.code,
        error_message=exc.message
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.to_dict(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc) -> JSONResponse:
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Resource not found: {request.url.path}"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc) -> JSONResponse:
    """Handle 500 Internal Server errors."""
    logger.error("internal_server_error", error=str(exc), path=request.url.path)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


# ============== Health & Root Routes ==============

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "documentation": "/api/v1/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint."""
    services = [
        ServiceHealth(name="API", status="healthy", latency_ms=0.1),
        ServiceHealth(name="Cache", status="healthy" if cache_manager else "degraded")
    ]
    
    uptime = time.time() - APP_START_TIME
    overall_status = "healthy" if all(s.status == "healthy" for s in services) else "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        services=services,
        uptime_seconds=round(uptime, 2)
    )


# ============== Include Routers with API Versioning ==============

app.include_router(stocks.router, prefix="/api/v1")
app.include_router(crypto.router, prefix="/api/v1")
app.include_router(commodities.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(websocket.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.is_development)
