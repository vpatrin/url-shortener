import secrets
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import Click, Link

# Redis

_pool = None


def _get_pool() -> redis.ConnectionPool:
    """Get or create Redis connection pool lazily."""
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(settings.REDIS_URL)
    return _pool


def _redis() -> redis.Redis:
    return redis.Redis(connection_pool=_get_pool())


async def _cache_link(code: str, url: str, ttl_seconds: int) -> None:
    await _redis().set(f"link:{code}", url, ex=ttl_seconds)


async def _get_cached_link(code: str) -> str | None:
    val = await _redis().get(f"link:{code}")
    return val.decode() if val else None


# Services


def generate_code() -> str:
    return secrets.token_urlsafe(settings.CODE_LENGTH)[:settings.CODE_LENGTH]


async def create_link(session: AsyncSession, url: str, ttl_hours: int | None = None) -> Link:
    ttl = ttl_hours if ttl_hours is not None else settings.DEFAULT_TTL_HOURS
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl)
    code = generate_code()

    link = Link(code=code, url=url, expires_at=expires_at)
    session.add(link)
    await session.commit()
    await session.refresh(link)

    ttl_seconds = int(timedelta(hours=ttl).total_seconds())
    await _cache_link(code, url, ttl_seconds)

    return link


async def resolve_link(session: AsyncSession, code: str) -> str | None:
    cached = await _get_cached_link(code)
    if cached:
        return cached

    result = await session.execute(select(Link).where(Link.code == code))
    link = result.scalar_one_or_none()

    if link is None:
        return None

    if link.expires_at < datetime.now(timezone.utc):
        return None

    remaining = int((link.expires_at - datetime.now(timezone.utc)).total_seconds())
    if remaining > 0:
        await _cache_link(code, link.url, remaining)

    return link.url


async def record_click(
    session: AsyncSession,
    code: str,
    ip: str | None,
    user_agent: str | None,
    referer: str | None,
) -> None:
    result = await session.execute(select(Link).where(Link.code == code))
    link = result.scalar_one_or_none()
    if link is None:
        return

    click = Click(link_id=link.id, ip=ip, user_agent=user_agent, referer=referer)
    link.click_count += 1
    session.add(click)
    await session.commit()


async def get_link_stats(session: AsyncSession, code: str) -> Link | None:
    result = await session.execute(
        select(Link).where(Link.code == code).options(selectinload(Link.clicks))
    )
    return result.scalar_one_or_none()
