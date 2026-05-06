from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "zmart_booking"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "zmart_booking"
    database_user: str = "postgres"
    database_password: str = "postgres"
    database_url_override: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ZMART_BOOKING_",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override

        return (
            "postgresql+psycopg://"
            f"{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

