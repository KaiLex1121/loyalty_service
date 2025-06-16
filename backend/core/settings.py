import os
from functools import lru_cache  # Для кэширования экземпляра настроек
from pathlib import Path

from pydantic import AnyHttpUrl, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # -> . (корень проекта)


class TrialPlanSettings(BaseSettings):
    DEFAULT_DURATION_DAYS: int
    INTERNAL_NAME: str

    model_config = SettingsConfigDict(env_prefix="TRIAL_")


class ServerSettings(BaseSettings):
    HOST: str
    PORT: int
    RELOAD: bool

    model_config = SettingsConfigDict(env_prefix="SERVER_")


class DatabaseSettings(BaseSettings):
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int
    DB: str
    TYPE: str
    ASYNC_DRIVER: str

    @computed_field
    @property
    def DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme=f"{self.TYPE}+{self.ASYNC_DRIVER}",
            username=self.USER,
            password=self.PASSWORD,
            host=self.HOST,
            port=self.PORT,
            path=self.DB,
        )

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")


class RedisSettings(BaseSettings):
    HOST: str
    PORT: int
    PASSWORD: str
    DB: int

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class ApiSettings(BaseSettings):
    TITLE: str
    VERSION: str
    DEBUG: bool
    DOCS_URL: str
    OPENAPI_URL: str
    REDOC_URL: str

    model_config = SettingsConfigDict(env_prefix="API_")


class SecuritySettings(BaseSettings):
    JWT_SECRET_KEY: str
    ALGORITHM: str
    HMAC_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    OTP_EXPIRE_MINUTES: int
    OTP_LENGTH: int

    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class WebAppSettings(BaseSettings):
    BASE_URL: AnyHttpUrl = "http://localhost:8000"
    TEMPLATES_DIR: Path = BASE_DIR / "backend" / "web_app" / "templates"
    STATIC_DIR: Path = BASE_DIR / "backend" / "web_app" / "static"


class AppSettings(BaseSettings):
    API: ApiSettings
    SECURITY: SecuritySettings
    SERVER: ServerSettings
    DB: DatabaseSettings
    WEB_APP: WebAppSettings
    REDIS: RedisSettings
    TRIAL_PLAN: TrialPlanSettings

    model_config = SettingsConfigDict(
        env_file=".env.test" if os.getenv("TEST_MODE") == "true" else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings(
        API=ApiSettings(),
        SECURITY=SecuritySettings(),
        SERVER=ServerSettings(),
        DB=DatabaseSettings(),
        WEB_APP=WebAppSettings(),
        REDIS=RedisSettings(),
        TRIAL_PLAN=TrialPlanSettings(),
    )


settings = get_settings()
