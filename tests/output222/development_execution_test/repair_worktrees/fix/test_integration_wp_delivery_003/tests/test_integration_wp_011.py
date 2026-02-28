import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.usermanagementservice import UserManagerService
from app.models import User
from unittest.mock import patch, MagicMock

client = TestClient(app)

class TestGetUserById:
    @pytest.fixture(autouse=True)
    def setup_user_service_mock(self):
        with patch('app.services.usermanagementservice.UserManagerService') as mock_service:
            self.mock_service_class = mock_service
            self.mock_service_instance = MagicMock()
            mock_service.return_value = self.mock_service_instance
            yield

    def test_get_user_by_id_success(self):
        user_data = {
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com",
            "created_at": "2023-01-01T00:00:00"
        }
        mock_user = User(**user_data)
        self.mock_service_instance.get_user_by_id.return_value = mock_user

        response = client.get("/api/v1/users/123")
        
        assert response.status_code == 200
        assert response.json() == user_data

    def test_get_user_by_id_not_found(self):
        self.mock_service_instance.get_user_by_id.return_value = None

        response = client.get("/api/v1/users/999")
        
        assert response.status_code == 404
        assert response.json() == {"detail": "User not found"}

    def test_get_user_by_id_invalid_id_format(self):
        response = client.get("/api/v1/users/invalid-id")
        
        assert response.status_code == 422

    def test_get_user_by_id_service_exception(self):
        self.mock_service_instance.get_user_by_id.side_effect = Exception("Database connection failed")

        response = client.get("/api/v1/users/123")
        
        assert response.status_code == 500
        assert "detail" in response.json()