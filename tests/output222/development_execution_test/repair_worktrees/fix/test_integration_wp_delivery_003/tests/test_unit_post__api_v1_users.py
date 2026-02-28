import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.services.usermanagementservice import UserManagementService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User

@pytest.fixture(scope="function")
def test_client():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def test_post_users_success(test_client, db_session, monkeypatch):
    def mock_create_user(*args, **kwargs):
        return User(id=1, username="testuser", email="test@example.com", created_at=None)
    monkeypatch.setattr(UserManagementService, "create_user", mock_create_user)
    
    response = test_client.post(
        "/api/v1/users",
        json={"username": "testuser", "email": "test@example.com", "password": "securepass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_post_users_validation_error(test_client):
    response = test_client.post(
        "/api/v1/users",
        json={"username": "", "email": "invalid-email", "password": "short"}
    )
    assert response.status_code == 422

def test_post_users_internal_error(test_client, monkeypatch):
    def mock_create_user(*args, **kwargs):
        raise Exception("Database connection failed")
    monkeypatch.setattr(UserManagementService, "create_user", mock_create_user)
    
    response = test_client.post(
        "/api/v1/users",
        json={"username": "testuser", "email": "test@example.com", "password": "securepass"}
    )
    assert response.status_code == 500