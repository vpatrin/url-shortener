"""Service layer tests."""

from datetime import datetime, timezone

import pytest

from app.services import create_link, generate_code, get_link_stats, resolve_link


@pytest.mark.unit
def test_generate_code():
    """Test that generate_code creates a code of correct length."""
    code = generate_code()
    assert isinstance(code, str)
    assert len(code) == 6  # Default CODE_LENGTH


@pytest.mark.integration
async def test_create_link(session):
    """Test creating a link."""
    url = "https://www.example.com"
    ttl_hours = 24

    link = await create_link(session, url, ttl_hours)

    assert link.url == url
    assert len(link.code) == 6
    assert link.expires_at > datetime.now(timezone.utc)
    assert link.click_count == 0


@pytest.mark.integration
async def test_resolve_link(session):
    """Test resolving a link."""
    url = "https://www.example.com"
    link = await create_link(session, url, 24)

    resolved_url = await resolve_link(session, link.code)
    assert resolved_url == url


@pytest.mark.integration
async def test_resolve_nonexistent_link(session):
    """Test resolving a non-existent link returns None."""
    resolved_url = await resolve_link(session, "nonexistent")
    assert resolved_url is None


@pytest.mark.integration
async def test_get_link_stats(session):
    """Test getting link statistics."""
    url = "https://www.example.com"
    link = await create_link(session, url, 24)

    stats = await get_link_stats(session, link.code)

    assert stats is not None
    assert stats.code == link.code
    assert stats.url == url
    assert stats.click_count == 0
    assert len(stats.clicks) == 0


@pytest.mark.integration
async def test_get_stats_nonexistent_link(session):
    """Test getting stats for non-existent link returns None."""
    stats = await get_link_stats(session, "nonexistent")
    assert stats is None
