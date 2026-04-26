"""Pydantic Settings — env-driven configuration for rfq_copilot_ms."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    DATABASE_URL: str = "sqlite:///./rfq_copilot.db"
    APP_ENV: str = "development"
    APP_PORT: int = 8003
    APP_DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Auth bypass — DEV ONLY. Replaced when IAM lands.
    AUTH_BYPASS_ENABLED: bool = True
    AUTH_BYPASS_USER_ID: str = "v1-demo-user"
    AUTH_BYPASS_USER_NAME: str = "System"
    AUTH_BYPASS_ROLE: str = "estimation_dept_lead"
    AUTH_BYPASS_DEBUG_HEADERS_ENABLED: bool = False

    # Declared but unused in Batch 3 — wired in Batch 5+.
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = ""
    AZURE_OPENAI_INTENT_DEPLOYMENT: str = ""
    AZURE_OPENAI_TIMEOUT_SECONDS: float = 30.0
    MANAGER_BASE_URL: str = ""
    INTELLIGENCE_BASE_URL: str = ""
    IAM_SERVICE_URL: str = ""


settings = Settings()
