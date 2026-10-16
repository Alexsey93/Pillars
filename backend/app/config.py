from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/pillars_db"
    db_echo: bool = False
    app_title: str = "Pillars API"

    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60


settings = Settings()