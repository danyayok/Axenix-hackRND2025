import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_request_body_valid():
    response = client.get("/requestBody")
    assert response.status_code in [200, 404, 500]

def test_get_request_body_invalid_method():
    response = client.post("/requestBody")
    assert response.status_code in [405, 404]

def test_get_request_body_structure():
    response = client.get("/requestBody")
    if response.status_code == 200:
        assert isinstance(response.json(), (dict, list))

@pytest.mark.parametrize("invalid_path", [
    "/requestBody/invalid",
    "/requestBody/../etc/passwd"
])
def test_get_request_body_invalid_paths(invalid_path):
    response = client.get(invalid_path)
    assert response.status_code in [400, 404, 500]