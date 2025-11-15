import pytest
from unittest.mock import patch, MagicMock
from backend.app.main import app
from backend.app.api.auth import create_access_token
from fastapi.testclient import TestClient

client = TestClient(app)

@pytest.fixture
def mock_db():
    with patch("backend.app.api.auth.get_db") as mock:
        yield mock

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.is_active = True
    user.is_admin = False
    return user

def test_database_integration_flow(mock_db, mock_user):
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    token = create_access_token(data={"sub": mock_user.username})
    response = client.get("/metrics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_database_error_propagation(mock_db):
    mock_db.return_value.__enter__.side_effect = Exception("DB connection failed")
    response = client.post("/token/guest")
    assert response.status_code == 500

def test_transaction_consistency(mock_db, mock_user):
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.commit.side_effect = Exception("Commit failed")

    token = create_access_token(data={"sub": mock_user.username})
    response = client.post("/1/read-all", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 500
    mock_db.rollback.assert_called_once()

def test_performance_under_load(mock_db, mock_user):
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    token = create_access_token(data={"sub": mock_user.username})
    responses = []
    for _ in range(100):
        response = client.get("/metrics", headers={"Authorization": f"Bearer {token}"})
        responses.append(response.status_code)
    assert all(status == 200 for status in responses)

def test_recovery_from_failures(mock_db, mock_user):
    mock_db.return_value.__enter__.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.commit.side_effect = [Exception("Failure"), None]

    token = create_access_token(data={"sub": mock_user.username})
    response1 = client.post("/1/read-all", headers={"Authorization": f"Bearer {token}"})
    response2 = client.post("/1/read-all", headers={"Authorization": f"Bearer {token}"})
    assert response1.status_code == 500
    assert response2.status_code == 200