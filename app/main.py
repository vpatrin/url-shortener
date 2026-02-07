from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.config import settings
from app.models import get_session, init_db
from app.schemas import ClickDetail, ShortenRequest, ShortenResponse, StatsResponse
from app.services import create_link, get_link_stats, record_click, resolve_link

_INDEX_HTML = (Path(__file__).parent / "static" / "index.html").read_text()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="URL Shortener", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.get("/", response_class=HTMLResponse)
async def index():
    return _INDEX_HTML


@app.post("/shorten", response_model=ShortenResponse)
@limiter.limit("10/minute")
async def shorten(
    request: Request,
    body: ShortenRequest,
    session: AsyncSession = Depends(get_session),
):
    link = await create_link(session, str(body.url), body.ttl_hours)
    return ShortenResponse(
        short_url=f"{settings.BASE_URL}/{link.code}",
        code=link.code,
        expires_at=link.expires_at,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/stats/{code}", response_model=StatsResponse)
async def stats(code: str, session: AsyncSession = Depends(get_session)):
    link = await get_link_stats(session, code)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return StatsResponse(
        code=link.code,
        url=link.url,
        created_at=link.created_at,
        expires_at=link.expires_at,
        click_count=link.click_count,
        clicks=[
            ClickDetail(
                clicked_at=c.clicked_at,
                ip=c.ip,
                user_agent=c.user_agent,
                referer=c.referer,
            )
            for c in link.clicks
        ],
    )


@app.get("/{code}")
async def redirect(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    url = await resolve_link(session, code)
    if url is None:
        raise HTTPException(status_code=404, detail="Link not found or expired")

    background_tasks.add_task(
        record_click,
        session,
        code,
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
        request.headers.get("referer"),
    )
    return RedirectResponse(url=url, status_code=301)
