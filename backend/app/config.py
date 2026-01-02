"""
CodeProof Configuration
Uses pydantic-settings to load from environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Problem Storage
    PROBLEM_DATA_ROOT: str = "/var/codeproof/problems"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:8000"

    # Admin (for initial setup)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables (compiler paths, etc.)

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


# Create settings instance
settings = Settings()
