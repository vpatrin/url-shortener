from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ShortenRequest(BaseModel):
    url: HttpUrl
    ttl_hours: int | None = None


class ShortenResponse(BaseModel):
    short_url: str
    code: str
    expires_at: datetime


class ClickDetail(BaseModel):
    clicked_at: datetime
    ip: str | None
    user_agent: str | None
    referer: str | None


class StatsResponse(BaseModel):
    code: str
    url: str
    created_at: datetime
    expires_at: datetime
    click_count: int
    clicks: list[ClickDetail]
