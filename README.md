# url-shortener

A fast URL shortener built with FastAPI, PostgreSQL, and Redis. Deployed with Docker Compose and Caddy.

## Local Development

### Prerequisites

- Python 3.12+
- Poetry
- Docker & Docker Compose

### Setup

1. **Install dependencies**

```bash
poetry install
```

1. **Start PostgreSQL and Redis**

```bash
docker compose -f docker-compose.dev.yml up -d
```

1. **Configure environment**

```bash
cp .env.local .env
```

1. **Run the application**

```bash
# With hot reload for development
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using environment variables directly
export $(cat .env.local | xargs) && poetry run uvicorn app.main:app --reload
```

1. **Access the application**

- Frontend: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### Development Commands

```bash
# Run tests
poetry run pytest

# Format code
poetry run black app/

# Lint code
poetry run ruff check app/

# Stop databases
docker compose -f docker-compose.dev.yml down

# View logs
docker compose -f docker-compose.dev.yml logs -f
```

## Production Deployment

For production deployment with Docker Compose and Caddy, use the main `docker-compose.yml` file.
