import os
from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQSettings(BaseSettings):
    USER: str
    PASSWORD: str
    HOST: str
    PORT: int

    @computed_field
    @property
    def RABBITMQ_URI(self) -> str:
        return f"amqp://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/"

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")


class RedisSettings(BaseSettings):
    HOST: str
    PORT: int
    PASSWORD: str
    DB: int

    @computed_field
    @property
    def REDIS_URI(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class ApiSettings(BaseSettings):
    INTERNAL_KEY: str
    INTERNAL_CORE_BASE_URL: str
    GATEWAY_BASE_URL: str

    model_config = SettingsConfigDict(env_prefix="API_")


class SecuritySettings(BaseSettings):
    JWT_SECRET_KEY: str
    ALGORITHM: str
    HMAC_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    OTP_EXPIRE_MINUTES: int
    OTP_LENGTH: int

    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class AppSettings(BaseSettings):
    API: ApiSettings
    REDIS: RedisSettings
    RABBITMQ: RabbitMQSettings
    SECURITY: SecuritySettings

    model_config = SettingsConfigDict(
        env_file=".env.test" if os.getenv("TEST_MODE") == "true" else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings(
        API=ApiSettings(),
        REDIS=RedisSettings(),
        RABBITMQ=RabbitMQSettings(),
        SECURITY=SecuritySettings(),
    )


settings = get_settings()
