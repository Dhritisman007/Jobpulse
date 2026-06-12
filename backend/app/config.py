"""Application configuration via environment variables."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """App settings loaded from .env file or environment variables."""

    # --- Paths ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DB_PATH: str = Field(default="jobs.db", description="SQLite database file path")
    RESUME_PATH: str = Field(default="resume.json", description="Path to resume JSON file")

    # --- API Keys (optional) ---
    ANTHROPIC_API_KEY: str = Field(default="", description="Claude API key for cover letters")
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Telegram bot token")
    TELEGRAM_CHAT_ID: str = Field(default="", description="Telegram chat ID for notifications")

    # --- Email (optional) ---
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    NOTIFICATION_EMAIL: str = Field(default="", description="Email to send digest to")

    # --- Scraping ---
    SCRAPE_INTERVAL_HOURS: int = Field(default=6, description="Hours between auto-scrapes")
    MAX_JOB_AGE_DAYS: int = Field(default=7, description="Only keep jobs posted within N days")
    NOTIFICATION_HOUR: int = Field(default=9, description="Hour of day (0-23) to send digest")

    # --- Optional API sources ---
    ADZUNA_APP_ID: str = Field(default="")
    ADZUNA_APP_KEY: str = Field(default="")
    RAPIDAPI_KEY: str = Field(default="", description="RapidAPI key for JSearch")

    # --- Frontend ---
    FRONTEND_URL: str = Field(default="http://localhost:5173")

    @property
    def database_url(self) -> str:
        db_file = self.BASE_DIR / self.DB_PATH
        return f"sqlite+aiosqlite:///{db_file}"

    @property
    def resume_file(self) -> Path:
        return self.BASE_DIR / self.RESUME_PATH

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
