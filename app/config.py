from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/shortener"
    REDIS_URL: str = "redis://redis:6379/0"
    BASE_URL: str = "https://s.victorpatrin.dev"
    DEFAULT_TTL_HOURS: int = 24
    CODE_LENGTH: int = 6

    model_config = {"env_file": ".env"}


settings = Settings()
