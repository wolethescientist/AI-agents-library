"""
Configuration management using Pydantic Settings.
Loads and validates environment-based configuration.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import logging


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    api_version: str = Field(default="v1", description="API version")
    
    # Performance Settings
    request_timeout: int = Field(
        default=15,
        ge=1,
        le=60,
        description="Maximum timeout for AI generation requests in seconds"
    )
    max_message_length: int = Field(
        default=5000,
        ge=1,
        le=10000,
        description="Maximum length for user messages"
    )
    
    # Concurrency Settings
    max_concurrent_requests: int = Field(
        default=1000,
        ge=10,
        le=2000,
        description="Maximum concurrent AI requests (semaphore limit)"
    )
    thread_pool_workers: int = Field(
        default=1000,
        ge=10,
        le=3000,
        description="Thread pool size for blocking Gemini API calls"
    )
    
    # Server Settings
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Rate Limiting Settings
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting middleware"
    )
    rate_limit_per_ip: int = Field(
        default=1000,
        ge=1,
        le=100000,
        description="Maximum requests per IP per minute"
    )
    rate_limit_global: int = Field(
        default=1000,
        ge=1,
        le=100000,
        description="Maximum total requests per minute (global)"
    )
    
    # Application Metadata
    app_name: str = Field(
        default="Multi-Agent Learning Chat API",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level is a valid logging level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @validator('gemini_api_key')
    def validate_api_key(cls, v):
        """Validate API key is not empty."""
        if not v or not v.strip():
            raise ValueError("gemini_api_key cannot be empty")
        return v.strip()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """
    Get application settings instance.
    This function can be used as a dependency in FastAPI.
    """
    return Settings()


def configure_logging(settings: Settings) -> None:
    """Configure application logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
