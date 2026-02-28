import pytest
from fastapi.testclient import TestClient
from app.services.documentstorageservice import DocumentStorageService
from app.database import Base, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(test_engine)

@pytest.fixture
def document_storage_service(db_session):
    return DocumentStorageService(db_session)

def test_document_storage_service_initialization(document_storage_service):
    assert document_storage_service is not None

def test_document_storage_service_has_required_methods(document_storage_service):
    assert hasattr(document_storage_service, 'store_document')
    assert hasattr(document_storage_service, 'retrieve_document')
    assert hasattr(document_storage_service, 'delete_document')
    assert hasattr(document_storage_service, 'list_documents')