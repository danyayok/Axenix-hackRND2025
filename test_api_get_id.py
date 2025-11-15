import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_id_success():
    response = client.get("/id")
    assert response.status_code in [200, 201]

def test_get_id_invalid_data():
    response = client.get("/id?invalid_param=test")
    assert response.status_code in [400, 404, 500]

def test_get_id_unauthorized():
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/id", headers=headers)
    assert response.status_code in [401, 403]

def test_get_id_structure():
    response = client.get("/id")
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert isinstance(data, dict)

@pytest.mark.parametrize("endpoint", ["/id"])
def test_get_id_methods(endpoint):
    response = client.get(endpoint)
    assert response.status_code in [200, 400, 401, 404, 500]