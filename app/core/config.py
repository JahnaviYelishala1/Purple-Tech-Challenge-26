from functools import lru_cache

from pydantic import Field, model_validator
from sqlalchemy.engine import make_url
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`.

    The field names stay Pythonic, while `validation_alias` maps them to the
    required uppercase environment variables.
    """

    database_url: str = Field(
        default="postgresql+psycopg2://store_intelligence:store_intelligence@"
        "localhost:5432/store_intelligence",
        validation_alias="DATABASE_URL",
    )
    app_name: str = Field(default="Store Intelligence Platform", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    demo_seed_on_startup: bool = Field(default=False, validation_alias="DEMO_SEED_ON_STARTUP")
    pos_conversion_window_minutes: int = Field(default=30, validation_alias="POS_CONVERSION_WINDOW_MINUTES")

    @model_validator(mode="after")
    def reject_ephemeral_production_sqlite(self) -> "Settings":
        """Avoid silently running production on disposable SQLite storage."""

        if self.environment.lower() == "production":
            drivername = make_url(self.database_url).drivername
            if drivername.startswith("sqlite"):
                raise ValueError("Production DATABASE_URL must point to persistent Postgres, not SQLite.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the shared settings instance."""

    return Settings()


settings = get_settings()
