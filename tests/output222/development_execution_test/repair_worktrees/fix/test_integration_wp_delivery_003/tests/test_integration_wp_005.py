import pytest
from app.services.usermanagementservice import UserManagementService
from app.database import get_db_session
from app.models import User, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def user_service(test_db):
    db_session = test_db()
    service = UserManagementService(db_session)
    yield service
    db_session.close()

def test_user_management_service_initialization(user_service):
    assert hasattr(user_service, 'db')
    assert user_service.db is not None

def test_create_user(user_service):
    user = user_service.create_user(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"

def test_get_user_by_id(user_service):
    created_user = user_service.create_user(
        username="testuser2",
        email="test2@example.com",
        password_hash="hashed_password2"
    )
    retrieved_user = user_service.get_user_by_id(created_user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == "testuser2"

def test_get_user_by_email(user_service):
    user_service.create_user(
        username="testuser3",
        email="test3@example.com",
        password_hash="hashed_password3"
    )
    retrieved_user = user_service.get_user_by_email("test3@example.com")
    assert retrieved_user is not None
    assert retrieved_user.email == "test3@example.com"

def test_update_user(user_service):
    user = user_service.create_user(
        username="testuser4",
        email="test4@example.com",
        password_hash="hashed_password4"
    )
    updated_user = user_service.update_user(
        user_id=user.id,
        username="updateduser",
        email="updated@example.com"
    )
    assert updated_user.username == "updateduser"
    assert updated_user.email == "updated@example.com"

def test_delete_user(user_service):
    user = user_service.create_user(
        username="testuser5",
        email="test5@example.com",
        password_hash="hashed_password5"
    )
    result = user_service.delete_user(user.id)
    assert result is True
    assert user_service.get_user_by_id(user.id) is None

def test_list_users(user_service):
    user_service.create_user(
        username="testuser6",
        email="test6@example.com",
        password_hash="hashed_password6"
    )
    user_service.create_user(
        username="testuser7",
        email="test7@example.com",
        password_hash="hashed_password7"
    )
    users = user_service.list_users()
    assert len(users) >= 2

def test_user_service_db_session_interaction(user_service):
    with patch('app.services.usermanagementservice.get_db_session') as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        user_service.create_user(
            username="testuser8",
            email="test8@example.com",
            password_hash="hashed_password8"
        )
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()