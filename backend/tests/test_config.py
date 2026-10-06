from backend.app.core.config import (
    AppEnvironment,
    settings,
)


def test_settings_load() -> None:
    assert settings.app_name == "SSM V4"
    assert settings.app_version == "0.1.0"

    assert settings.app_env in {
        AppEnvironment.DEVELOPMENT,
        AppEnvironment.STAGING,
        AppEnvironment.PRODUCTION,
    }


def test_supabase_settings_exist() -> None:
    assert str(settings.supabase_url)
    assert settings.supabase_anon_key
    assert settings.supabase_service_role_key


def test_database_url_exists() -> None:
    assert settings.database_url
    assert settings.sqlalchemy_database_url.startswith("postgresql+psycopg://")


def test_log_level() -> None:
    assert settings.log_level in {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }
