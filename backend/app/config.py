"""
Central application settings.

Why this exists: every credential and environment-specific value (DB URL,
LLM API key/model, allowed CORS origins) must come from the environment,
never be hardcoded in source. pydantic-settings reads from a `.env` file
locally and from real environment variables in production (Render/Railway),
so the same code runs in both places unchanged.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    cors_origins: str = "http://localhost:5173"
    environment: str = "development"

    # Optional - only required for scripts/send_digest.py. Left blank by
    # default so the main app runs fine without ever configuring email.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    digest_recipient: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    # Cached so we parse the environment once per process, not on every request.
    return Settings()