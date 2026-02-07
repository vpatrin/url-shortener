# url-shortener

A fast URL shortener built with FastAPI, PostgreSQL, and Redis. Deployed with Docker Compose and Caddy.

## ⚡ Quick Start

```bash
# Setup and start everything
make dev

# Run the application
make run
```

Access the application at <http://localhost:8000>

## 📋 Prerequisites

- Python 3.12+
- Poetry
- Docker & Docker Compose
- Make

## 🛠️ Development

### Common Commands

```bash
make help          # Show all available commands

# Development
make dev           # Full setup (install deps + start databases)
make run           # Run the application with hot reload
make up            # Start databases only
make down          # Stop databases

# Testing
make test          # Run all tests
make test-cov      # Run tests with coverage report

# Code Quality
make lint          # Lint code with ruff
make format        # Format code with black
make check         # Run all checks

# Database
make db-shell      # Open PostgreSQL shell
make redis-shell   # Open Redis CLI
make logs          # Show database logs

# Cleanup
make clean         # Stop containers and clean up
```

### Manual Setup (without Make)

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
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points

- Frontend: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/health>

### Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
poetry run pytest tests/test_api.py

# Run tests by marker
poetry run pytest -m unit         # Unit tests only
poetry run pytest -m integration  # Integration tests only
```

The test suite includes:

- **Unit tests**: Service layer logic
- **Integration tests**: Full API endpoint tests with test database
- **Coverage reports**: HTML reports generated in `htmlcov/`

### Code Quality

This project follows professional Python standards:

```bash
# Format code (Black - 100 char line length)
make format

# Lint code (Ruff)
make lint

# Run all checks
make check
```

## 🏗️ Architecture

- **FastAPI**: Modern async web framework
- **PostgreSQL**: Relational database for links and clicks
- **Redis**: Cache layer for fast redirects
- **SQLAlchemy**: Async ORM
- **Slowapi**: Rate limiting

### Project Structure

```
url-shortener/
├── app/
│   ├── main.py           # FastAPI application & routes
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── services.py       # Business logic
│   ├── config.py         # Configuration
│   └── static/
│       └── index.html    # Frontend
├── tests/
│   ├── conftest.py       # Test fixtures
│   ├── test_api.py       # API tests
│   └── test_services.py  # Service tests
├── Makefile              # Development commands
├── docker-compose.yml    # Production setup
├── docker-compose.dev.yml # Development databases
└── pyproject.toml        # Dependencies & config
```

## 🚀 Production Deployment

For production deployment with Docker Compose and Caddy, use the main `docker-compose.yml` file.

```bash
make build   # Build production image
```

## 📝 Environment Variables

See [.env.example](.env.example) for all available configuration options.

Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `BASE_URL`: Base URL for shortened links
- `DEFAULT_TTL_HOURS`: Default expiration time (default: 24)
- `CODE_LENGTH`: Length of short codes (default: 6)
