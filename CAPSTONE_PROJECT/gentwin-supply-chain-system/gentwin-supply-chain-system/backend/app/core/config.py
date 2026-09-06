"""
Global application configuration.

Centralizes environment-driven settings using pydantic-settings so the
rest of the application never touches os.environ directly.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- App metadata ---
    PROJECT_NAME: str = "Generative AI & Digital Twin Supply Chain Resilience System"
    API_V1_PREFIX: str = "/api/v1"

    # --- Security / CORS ---
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Gemini model config ---
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash")

    # --- Optimizer defaults ---
    ALPHA_COST_WEIGHT: float = Field(
        default=0.1,
        description="Weight applied to the cost component in the Dijkstra weight function.",
    )
    DEFAULT_TTR_BASE_DAYS: float = Field(
        default=2.0,
        description="Baseline recovery time (days) added per disrupted node/edge when estimating TTR.",
    )

    # --- Auth ---
    SECRET_KEY: str = Field(default="dev-only-insecure-secret-change-me")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=120)
    DB_PATH: str = Field(default="./supply_chain_twin.db")
    DEFAULT_ADMIN_USERNAME: str = Field(default="admin")
    DEFAULT_ADMIN_PASSWORD: str = Field(default="Admin@123")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton across the app lifetime)."""
    return Settings()
