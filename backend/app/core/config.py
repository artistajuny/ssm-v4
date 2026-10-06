from enum import StrEnum
from functools import lru_cache

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    app_env: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        alias="APP_ENV",
    )

    app_name: str = Field(
        default="SSM V4",
        alias="APP_NAME",
    )

    app_version: str = Field(
        default="0.1.0",
        alias="APP_VERSION",
    )

    debug: bool = Field(
        default=False,
        alias="DEBUG",
    )

    supabase_url: HttpUrl = Field(
        alias="SUPABASE_URL",
    )

    supabase_anon_key: str = Field(
        alias="SUPABASE_ANON_KEY",
        min_length=1,
    )

    supabase_service_role_key: str = Field(
        alias="SUPABASE_SERVICE_ROLE_KEY",
        min_length=1,
    )

    database_url: str = Field(
        alias="DATABASE_URL",
        min_length=1,
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        valid_prefixes = (
            "postgresql://",
            "postgres://",
            "postgresql+psycopg://",
        )

        if not value.startswith(valid_prefixes):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection URL.")

        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()

        allowed_levels = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if normalized not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(sorted(allowed_levels))}")

        return normalized

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url

        if url.startswith("postgresql+psycopg://"):
            return url

        if url.startswith("postgresql://"):
            return url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        if url.startswith("postgres://"):
            return url.replace(
                "postgres://",
                "postgresql+psycopg://",
                1,
            )

        return url

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnvironment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        return self.app_env == AppEnvironment.STAGING

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnvironment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
