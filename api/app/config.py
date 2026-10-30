"""Settings loaded from the environment and the repo-root .env (A01)."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings. Model IDs are only ever read from here."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model_api_key: str | None = None
    meta_base_url: str = "https://api.meta.ai/v1"
    cors_origins: str = "http://localhost:3000"
    model_read: str = "muse-spark-1.3"
    model_impact: str = "muse-wonder-1.0"
    model_transcribe: str = "muse-voice-transcribe-1.0"
    demo_mode: Literal["live", "replay"] = "live"


def get_settings() -> Settings:
    """Build settings from the current environment (read per request)."""
    return Settings()
