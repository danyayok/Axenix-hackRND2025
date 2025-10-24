from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Axenix Conf Backend"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8090

    # SQLite (async)
    database_url: str = "sqlite+aiosqlite:///./axenix.db"

    public_base_url: str = "http://localhost:8090"

    # JWT
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_ttl_seconds: int = 24 * 3600  # 24h

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        extra="ignore",
    )

settings = Settings()
