import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.usermanagementservice import UserManagementService
from unittest.mock import patch, MagicMock

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_user_service():
    with patch('app.services.usermanagementservice.UserManagementService') as mock:
        yield mock

def test_get_user_by_id_success(test_client, mock_user_service):
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user_service.get_user_by_id.return_value = mock_user
    response = test_client.get("/api/v1/users/123")
    assert response.status_code == 200
    assert response.json() == {
        "id": 123,
        "username": "testuser",
        "email": "test@example.com"
    }

def test_get_user_by_id_not_found(test_client, mock_user_service):
    mock_user_service.get_user_by_id.return_value = None
    response = test_client.get("/api/v1/users/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_get_user_by_id_invalid_path_param(test_client):
    response = test_client.get("/api/v1/users/invalid_id")
    assert response.status_code == 422