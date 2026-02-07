"""API endpoint tests."""

import pytest


@pytest.mark.integration
async def test_health(client):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
async def test_index(client):
    """Test the index page returns HTML."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.integration
async def test_shorten_url(client):
    """Test creating a short URL."""
    payload = {"url": "https://www.example.com"}
    response = await client.post("/shorten", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "short_url" in data
    assert "code" in data
    assert "expires_at" in data
    assert len(data["code"]) == 6  # Default CODE_LENGTH


@pytest.mark.integration
async def test_shorten_url_with_custom_ttl(client):
    """Test creating a short URL with custom TTL."""
    payload = {"url": "https://www.example.com", "ttl_hours": 48}
    response = await client.post("/shorten", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "expires_at" in data


@pytest.mark.integration
async def test_redirect(client):
    """Test redirect functionality."""
    # First create a short URL
    payload = {"url": "https://www.example.com"}
    create_response = await client.post("/shorten", json=payload)
    code = create_response.json()["code"]

    # Then test the redirect
    response = await client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"] == "https://www.example.com"


@pytest.mark.integration
async def test_redirect_nonexistent(client):
    """Test redirect with non-existent code returns 404."""
    response = await client.get("/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_stats(client):
    """Test getting stats for a short URL."""
    # Create a short URL
    payload = {"url": "https://www.example.com"}
    create_response = await client.post("/shorten", json=payload)
    code = create_response.json()["code"]

    # Redirect once to create a click
    await client.get(f"/{code}", follow_redirects=False)

    # Get stats
    response = await client.get(f"/stats/{code}")
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == code
    assert data["url"] == "https://www.example.com"
    assert data["click_count"] >= 0
    assert "clicks" in data
    assert "created_at" in data
    assert "expires_at" in data


@pytest.mark.integration
async def test_stats_nonexistent(client):
    """Test getting stats for non-existent code returns 404."""
    response = await client.get("/stats/nonexistent")
    assert response.status_code == 404


@pytest.mark.integration
async def test_rate_limiting(client):
    """Test rate limiting on shorten endpoint."""
    payload = {"url": "https://www.example.com"}

    # Make 11 requests (limit is 10/minute)
    for i in range(11):
        response = await client.post("/shorten", json=payload)
        if i < 10:
            assert response.status_code == 200
        else:
            # 11th request should be rate limited
            assert response.status_code == 429
            assert "rate limit" in response.json()["detail"].lower()
