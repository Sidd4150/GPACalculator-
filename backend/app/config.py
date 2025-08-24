"""
Simple configuration for the GPA Calculator application.
"""

import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with sensible defaults."""

    # Application info (hardcoded - same across all environments)
    app_name: str = "GPA Calculator API"
    app_version: str = "1.0.0"
    app_description: str = "API for parsing USF transcript PDFs and calculating GPA"

    # Environment-specific settings (defaults provided, override via env vars)
    environment: str = "development"
    cors_origins: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default
    ]
    max_file_size_mb: int = 50

    # Server settings (hardcoded - same across environments)
    host: str = "0.0.0.0"  # Always bind to all interfaces
    port: int = 8000  # Default port for local development

    # Rate limiting settings (hardcoded - same across environments)
    rate_limit_upload: int = 10  # requests per minute
    rate_limit_gpa: int = 50  # requests per minute

    # Development constants (hardcoded)
    rate_limit_storage_uri: str = "memory://"  # For development/testing
    default_retry_after: int = 60  # seconds

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list, handling both string and list types."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return list(self.cors_origins) if self.cors_origins else []

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return os.getenv("TESTING", "false").lower() == "true"

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
