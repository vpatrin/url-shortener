"""Pytest configuration and shared fixtures with Testcontainers.

This uses Docker containers for PostgreSQL and Redis, ensuring:
- Complete isolation between test runs
- No manual database setup required
- Production-like environment
- CI/CD friendly
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.main import app
from app.models import Base


@pytest.fixture(scope="session")
def postgres_container():
    """
    Start a PostgreSQL container for the test session.
    The container is automatically stopped after all tests complete.
    """
    with PostgresContainer("postgres:16-alpine") as postgres:
        # Convert psycopg2 URL to asyncpg
        db_url = postgres.get_connection_url().replace("psycopg2", "asyncpg")
        yield db_url


@pytest.fixture(scope="session")
def redis_container():
    """
    Start a Redis container for the test session.
    The container is automatically stopped after all tests complete.
    """
    with RedisContainer("redis:7-alpine") as redis:
        redis_url = f"redis://{redis.get_container_host_ip()}:{redis.get_exposed_port(6379)}/0"
        yield redis_url


@pytest.fixture(scope="session")
def test_engine(postgres_container):
    """Create a test database engine using the testcontainer."""
    engine = create_async_engine(postgres_container, echo=False)
    return engine


@pytest.fixture(scope="function", autouse=True)
def setup_test_environment(postgres_container, redis_container, monkeypatch):
    """
    Override settings for each test to use testcontainers.
    autouse=True means this runs automatically for every test.
    """
    monkeypatch.setattr("app.config.settings.DATABASE_URL", postgres_container)
    monkeypatch.setattr("app.config.settings.REDIS_URL", redis_container)
    # Override environment variables as well
    monkeypatch.setenv("DATABASE_URL", postgres_container)
    monkeypatch.setenv("REDIS_URL", redis_container)


@pytest.fixture(scope="function")
async def test_db(test_engine):
    """
    Create all tables before each test and drop them after.
    This ensures each test starts with a clean database.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def session(test_engine, test_db):
    """Provide a database session for tests."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(session):
    """
    Provide an async HTTP client for testing the API.
    Overrides the database session dependency to use the test database.
    """
    from app.models import get_session

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
