from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Axenix Conf Backend"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8090

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )

settings = Settings()
