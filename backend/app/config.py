"""
Application Configuration Module
Handles all environment variables and application settings using Pydantic Settings.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings using Pydantic Settings for type-safe configuration.
    All settings are loaded from environment variables with sensible defaults.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = Field(default="Stock Prediction Dashboard API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode flag")
    environment: str = Field(default="development", description="Environment: development, staging, production")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    
    # API Keys
    metals_api_key: Optional[str] = Field(default=None, description="Metals-API key for commodity prices")
    alpha_vantage_key: Optional[str] = Field(default=None, description="Alpha Vantage API key")
    coingecko_api_key: Optional[str] = Field(default=None, description="CoinGecko API key (optional)")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis server host")
    redis_port: int = Field(default=6379, description="Redis server port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_ssl: bool = Field(default=False, description="Use SSL for Redis connection")
    cache_ttl: int = Field(default=300, description="Default cache TTL in seconds")
    
    # Model Paths
    model_base_path: str = Field(default="ml-models/saved_models", description="Base path for ML models")
    stock_model_path: str = Field(default="ml-models/saved_models/stock_lstm.h5", description="Stock LSTM model path")
    crypto_model_path: str = Field(default="ml-models/saved_models/crypto_lstm.h5", description="Crypto LSTM model path")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="API rate limit per minute")
    rate_limit_per_hour: int = Field(default=1000, description="API rate limit per hour")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or console")
    
    # Market Settings
    default_market: str = Field(default="NSE", description="Default stock market (NSE/BSE)")
    market_timezone: str = Field(default="Asia/Kolkata", description="Market timezone")
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v.lower()
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v.upper()
    
    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL."""
        protocol = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache for performance - settings are only loaded once.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Export settings instance for convenience
settings = get_settings()
