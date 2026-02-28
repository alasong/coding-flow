import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.usermanagementservice import UserManagementService
from app.models import UserCreate
from app.database import get_db
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_user_management_service():
    with patch('app.services.usermanagementservice.UserManagementService') as mock:
        instance = mock.return_value
        instance.create_user.return_value = MagicMock(
            id=1,
            email="test@example.com",
            full_name="Test User",
            created_at="2023-01-01T00:00:00"
        )
        yield instance

def test_post_users_success(mock_user_management_service, mock_db_session):
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    }
    
    with patch('app.main.get_db', return_value=mock_db_session):
        with patch('app.main.UserManagementService', return_value=mock_user_management_service):
            response = client.post("/api/v1/users", json=user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "created_at" in data

def test_post_users_validation_error():
    invalid_user_data = {
        "email": "invalid-email",
        "full_name": "",
        "password": "short"
    }
    
    response = client.post("/api/v1/users", json=invalid_user_data)
    assert response.status_code == 422

def test_post_users_service_exception():
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "securepassword123"
    }
    
    with patch('app.main.UserManagementService') as mock_service_class:
        mock_service = MagicMock()
        mock_service.create_user.side_effect = Exception("Database connection failed")
        mock_service_class.return_value = mock_service
        
        response = client.post("/api/v1/users", json=user_data)
    
    assert response.status_code == 500
    assert "detail" in response.json()

def test_post_users_integration_with_database_dependency():
    user_data = {
        "email": "integration@test.com",
        "full_name": "Integration Test",
        "password": "integrationpass123"
    }
    
    with patch('app.main.get_db') as mock_get_db:
        mock_db = MagicMock(spec=Session)
        mock_get_db.return_value = mock_db
        
        with patch('app.main.UserManagementService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_user.return_value = MagicMock(
                id=2,
                email="integration@test.com",
                full_name="Integration Test",
                created_at="2023-01-01T00:00:00"
            )
            mock_service_class.return_value = mock_service
            
            response = client.post("/api/v1/users", json=user_data)
    
    assert response.status_code == 200
    assert response.json()["email"] == "integration@test.com"

def test_post_users_content_type_header():
    user_data = {
        "email": "header@test.com",
        "full_name": "Header Test",
        "password": "headerpass123"
    }
    
    response = client.post(
        "/api/v1/users",
        json=user_data,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")