import pytest
from fastapi.testclient import TestClient
from app.services.documentsearchservice import DocumentSearchService
from app.database import Base, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def document_search_service(db_session):
    return DocumentSearchService(db_session)

def test_document_search_service_initialization(document_search_service):
    assert document_search_service is not None

def test_document_search_service_search_method_exists(document_search_service):
    assert hasattr(document_search_service, 'search')
    assert callable(getattr(document_search_service, 'search'))

def test_document_search_service_search_returns_list(document_search_service):
    result = document_search_service.search(query="", filters={})
    assert isinstance(result, list)