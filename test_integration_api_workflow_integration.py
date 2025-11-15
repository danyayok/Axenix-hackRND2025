import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture
def mock_dependencies():
    with patch("backend.app.api.auth.authenticate_user") as mock_auth, \
         patch("backend.app.api.chat.process_message") as mock_chat, \
         patch("backend.app.api.notifications.send_notification") as mock_notify:
        mock_auth.return_value = {"user_id": 1, "role": "user"}
        mock_chat.return_value = {"message_id": 123, "content": "test"}
        mock_notify.return_value = True
        yield

def test_full_api_workflow_integration(mock_dependencies):
    auth_response = client.post("/login", json={"username": "test", "password": "pass"})
    assert auth_response.status_code == 200
    token = auth_response.json().get("token")
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}
    message_response = client.post("/test-room", json={"content": "integration test"}, headers=headers)
    assert message_response.status_code == 200
    message_data = message_response.json()
    assert "message_id" in message_data

    notification_response = client.post("/1/read/123", headers=headers)
    assert notification_response.status_code == 200
    assert notification_response.json() == {"status": "success"}

def test_error_propagation_in_workflow(mock_dependencies):
    with patch("backend.app.api.auth.authenticate_user", side_effect=Exception("Auth failed")):
        response = client.post("/login", json={"username": "test", "password": "wrong"})
        assert response.status_code == 500
        assert "Auth failed" in response.text

def test_transaction_consistency_on_failure(mock_dependencies):
    with patch("backend.app.api.notifications.send_notification", return_value=False):
        auth_response = client.post("/login", json={"username": "test", "password": "pass"})
        assert auth_response.status_code == 200
        token = auth_response.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        message_response = client.post("/test-room", json={"content": "rollback test"}, headers=headers)
        assert message_response.status_code == 500

def test_performance_under_load(mock_dependencies):
    import time
    start = time.time()
    for _ in range(10):
        response = client.post("/login", json={"username": "test", "password": "pass"})
        assert response.status_code == 200
    end = time.time()
    assert (end - start) < 2.0

def test_recovery_from_component_failure(mock_dependencies):
    with patch("backend.app.api.chat.process_message", side_effect=Exception("Chat service down")):
        auth_response = client.post("/login", json={"username": "test", "password": "pass"})
        assert auth_response.status_code == 200
        token = auth_response.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        message_response = client.post("/test-room", json={"content": "recovery test"}, headers=headers)
        assert message_response.status_code == 500

    mock_dependencies.chat.process_message.return_value = {"message_id": 456, "content": "recovered"}
    retry_response = client.post("/test-room", json={"content": "retry test"}, headers=headers)
    assert retry_response.status_code == 200
    assert "message_id" in retry_response.json()