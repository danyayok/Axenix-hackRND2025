from unittest.mock import AsyncMock, Mock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app, on_startup

@pytest.fixture
def client():
    return TestClient(app)

def test_root_redirects_to_docs(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.url.path == "/docs"

def test_favicon_returns_empty_content_with_204(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 204
    assert response.content == b""

@pytest.mark.asyncio
async def test_on_startup_creates_tables():
    with patch("app.main.engine.begin") as mock_engine_begin:
        mock_conn = AsyncMock()
        mock_engine_begin.return_value.__aenter__.return_value = mock_conn
        
        await on_startup()
        
        mock_conn.run_sync.assert_called_once()

def test_app_includes_all_routers():
    expected_prefixes = [
        "/api/rooms",
        "/api/users",
        "/api/participants",
        "/api/chat",
        "/api/state",
        "/api/auth",
        "/api/rtc",
        "/api/moderation",
        "/api/sync",
        "/api/crypto",
        "/api/covers",
        "/api/recordings",
        "/api/metrics",
        "/api/notifications"
    ]
    
    included_routes = [route.path for route in app.routes]
    
    for prefix in expected_prefixes:
        assert any(route.startswith(prefix) for route in included_routes), f"Router with prefix {prefix} not included"

def test_app_mounts_static_files():
    static_mounts = [mount for mount in app.router.routes if hasattr(mount, 'name') and mount.name == 'static']
    assert len(static_mounts) > 0, "Static files not mounted"

def test_app_initialization():
    assert isinstance(app, FastAPI)
    assert app.title == "app"
    assert app.version == "1.1.0"
    assert app.default_response_class.__name__ == "ORJSONResponse"
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"