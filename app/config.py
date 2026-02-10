from pydantic import Field, field_validator
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database configuration
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "shortener"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # Redis configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Connection URLs (auto-constructed from atomic values)
    DATABASE_URL: str = Field(default="")
    REDIS_URL: str = Field(default="")

    # Application configuration
    BASE_URL: str = "http://localhost:8000"
    DEFAULT_TTL_HOURS: int = 24
    CODE_LENGTH: int = 6

    model_config = {
        "env_file": os.getenv("ENV_FILE", ".env"),
        "extra": "ignore",
    }

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def construct_database_url(cls, v: str, info) -> str:
        if v:
            return v
        data = info.data
        return f"postgresql+asyncpg://{data['DB_USER']}:{data['DB_PASSWORD']}@{data['DB_HOST']}:{data['DB_PORT']}/{data['DB_NAME']}"

    @field_validator("REDIS_URL", mode="after")
    @classmethod
    def construct_redis_url(cls, v: str, info) -> str:
        if v:
            return v
        data = info.data
        return f"redis://{data['REDIS_HOST']}:{data['REDIS_PORT']}/{data['REDIS_DB']}"


settings = Settings()
