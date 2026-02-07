"""Pytest configuration and shared fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.main import app
from app.models import Base


# Test database URL (you can override with TEST_DATABASE_URL env var)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/shortener_test"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    return engine


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
