import pytest
from app.database import get_db_session
from app.models import User
from app.services.usermanagementservice import UserManagementService
from sqlalchemy.exc import IntegrityError
from datetime import datetime


class TestUsersDBIntegration:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        # Ensure test database is clean before each test
        session = get_db_session()
        try:
            session.query(User).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def test_create_user_persists_to_db(self):
        session = get_db_session()
        user_service = UserManagementService()
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": "hashed_pwd_123",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        user = user_service.create_user(**user_data)
        
        # Verify user is persisted
        retrieved_user = session.query(User).filter_by(username="testuser").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.hashed_password == "hashed_pwd_123"
        
        session.close()

    def test_get_user_by_username_returns_correct_user(self):
        session = get_db_session()
        user_service = UserManagementService()
        
        # Create user first
        user_service.create_user(
            username="gettest",
            email="gettest@example.com",
            hashed_password="hashed_pwd_456",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Retrieve user
        user = user_service.get_user_by_username("gettest")
        
        assert user is not None
        assert user.username == "gettest"
        assert user.email == "gettest@example.com"
        
        session.close()

    def test_get_user_by_email_returns_correct_user(self):
        session = get_db_session()
        user_service = UserManagementService()
        
        # Create user first
        user_service.create_user(
            username="emailtest",
            email="emailtest@example.com",
            hashed_password="hashed_pwd_789",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Retrieve user
        user = user_service.get_user_by_email("emailtest@example.com")
        
        assert user is not None
        assert user.username == "emailtest"
        assert user.email == "emailtest@example.com"
        
        session.close()

    def test_create_user_with_duplicate_username_fails(self):
        session = get_db_session()
        user_service = UserManagementService()
        
        # Create first user
        user_service.create_user(
            username="duplicate",
            email="first@example.com",
            hashed_password="pwd1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Attempt to create second user with same username
        with pytest.raises(IntegrityError):
            user_service.create_user(
                username="duplicate",
                email="second@example.com",
                hashed_password="pwd2",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        session.close()

    def test_user_management_service_interacts_with_db_models_correctly(self):
        session = get_db_session()
        user_service = UserManagementService()
        
        # Create user via service
        user = user_service.create_user(
            username="service_test",
            email="service@test.com",
            hashed_password="service_hash",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Verify model instance is properly constructed
        assert isinstance(user, User)
        assert user.username == "service_test"
        assert user.email == "service@test.com"
        
        # Verify session contains the user
        session_user = session.query(User).filter_by(id=user.id).first()
        assert session_user is not None
        assert session_user.username == "service_test"
        
        session.close()