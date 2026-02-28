import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User
from app.services.usermanagementservice import UserManagementService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture
def user_management_service(db_session):
    return UserManagementService(db_session)

def test_create_user(db_session, user_management_service):
    user = user_management_service.create_user(email="test@example.com", name="Test User")
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert db_session.query(User).filter(User.email == "test@example.com").first() is not None

def test_get_user_by_email(db_session, user_management_service):
    user_management_service.create_user(email="test2@example.com", name="Test User 2")
    retrieved = user_management_service.get_user_by_email("test2@example.com")
    assert retrieved is not None
    assert retrieved.email == "test2@example.com"

def test_get_user_by_id(db_session, user_management_service):
    user = user_management_service.create_user(email="test3@example.com", name="Test User 3")
    retrieved = user_management_service.get_user_by_id(user.id)
    assert retrieved is not None
    assert retrieved.id == user.id

def test_list_users(db_session, user_management_service):
    user_management_service.create_user(email="a@example.com", name="A")
    user_management_service.create_user(email="b@example.com", name="B")
    users = user_management_service.list_users()
    assert len(users) == 2

def test_delete_user(db_session, user_management_service):
    user = user_management_service.create_user(email="to_delete@example.com", name="To Delete")
    user_management_service.delete_user(user.id)
    assert db_session.query(User).filter(User.id == user.id).first() is None