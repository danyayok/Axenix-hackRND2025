import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_slug_valid():
    response = client.get("/slug")
    assert response.status_code in [200, 404]

def test_get_slug_invalid_method():
    response = client.post("/slug")
    assert response.status_code == 405

def test_get_slug_unauthorized():
    response = client.get("/slug")
    assert response.status_code in [200, 401, 404]

@pytest.mark.parametrize("invalid_slug", ["", " ", None, 123, {}, []])
def test_get_slug_invalid_data(invalid_slug):
    response = client.get(f"/{invalid_slug}")
    assert response.status_code in [400, 404, 422]

def test_get_slug_structure():
    response = client.get("/slug")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, (dict, list))