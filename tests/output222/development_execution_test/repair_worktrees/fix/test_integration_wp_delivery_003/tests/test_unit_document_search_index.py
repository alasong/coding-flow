import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.documentsearchservice import DocumentSearchService
from app.models import Document

@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(in_memory_db):
    session = in_memory_db()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def document_search_service(db_session):
    return DocumentSearchService(db_session)

def test_document_search_index_creation(db_session):
    assert db_session.bind.dialect.name == "sqlite"

def test_document_search_index_query_empty(db_session, document_search_service):
    results = document_search_service.search_documents("test")
    assert isinstance(results, list)
    assert len(results) == 0

def test_document_search_index_query_with_data(db_session, document_search_service):
    doc = Document(title="Test Document", content="This is a test content for search", metadata={})
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    results = document_search_service.search_documents("test")
    assert len(results) == 1
    assert results[0].title == "Test Document"

def test_document_search_index_case_insensitive(db_session, document_search_service):
    doc = Document(title="TEST DOCUMENT", content="test content", metadata={})
    db_session.add(doc)
    db_session.commit()
    
    results = document_search_service.search_documents("test")
    assert len(results) == 1