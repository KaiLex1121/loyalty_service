from pathlib import Path
from typing import Optional, List
from functools import lru_cache # Для кэширования экземпляра настроек

from pydantic import AnyHttpUrl, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent # -> . (корень проекта)


class ServerSettings(BaseSettings):
    HOST: str
    PORT: int
    RELOAD: bool

    model_config = SettingsConfigDict(env_prefix='SERVER_')


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

    model_config = SettingsConfigDict(env_prefix='POSTGRES_')


class RedisSettings(BaseSettings):
    HOST: str
    PORT: int
    PASSWORD: str
    DB: int

    model_config = SettingsConfigDict(env_prefix='REDIS_')


class ApiSettings(BaseSettings):
    NAME: str
    PREFIX: str
    DEBUG: bool
    DOCS_URL: Optional[AnyHttpUrl]
    OPENAPI_URL: Optional[AnyHttpUrl]
    REDOC_URL: Optional[AnyHttpUrl]

    model_config = SettingsConfigDict(env_prefix='API_')


class SecuritySettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(env_prefix='SECURITY_')


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

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

@lru_cache()
def get_config() -> AppSettings:
    return AppSettings(
        API=ApiSettings(),
        SECURITY=SecuritySettings(),
        SERVER=ServerSettings(),
        DB=DatabaseSettings(),
        WEB_APP=WebAppSettings(),
        REDIS=RedisSettings(),
    )


settings = get_config()