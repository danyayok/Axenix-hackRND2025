from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # базовые настройки
    app_name: str = "Axenix Conf Backend"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8090

    # SQLite (async) — файл в корне проекта
    database_url: str = "sqlite+aiosqlite:///./axenix.db"

    # база для генерации публичных ссылок (понадобится фронту)
    public_base_url: str = "http://localhost:8090"

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        extra="ignore",
    )

settings = Settings()
