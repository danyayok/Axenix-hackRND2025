import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_get_detail_success():
    response = client.get("/detail")
    assert response.status_code == 200

def test_get_detail_not_found():
    response = client.get("/nonexistent")
    assert response.status_code == 404

def test_get_detail_invalid_method():
    response = client.post("/detail")
    assert response.status_code == 405

def test_get_detail_unauthorized():
    response = client.get("/detail", headers={"Authorization": "InvalidToken"})
    assert response.status_code == 401

@pytest.mark.parametrize("endpoint", ["/detail", "/id", "/slug"])
def test_get_detail_various_endpoints(endpoint):
    response = client.get(endpoint)
    assert response.status_code in [200, 404]

def test_get_detail_response_structure():
    response = client.get("/detail")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)