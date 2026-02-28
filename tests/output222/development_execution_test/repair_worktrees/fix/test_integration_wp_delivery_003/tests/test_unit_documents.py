import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Document
from app.services.documentstorageservice import DocumentStorageService

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
def document_storage_service(db_session):
    return DocumentStorageService(db_session)

def test_document_storage_service_create_document(document_storage_service):
    doc = document_storage_service.create_document(
        title="Test Doc",
        content="Test content",
        file_path="/tmp/test.pdf",
        mime_type="application/pdf"
    )
    assert doc.id is not None
    assert doc.title == "Test Doc"
    assert doc.content == "Test content"
    assert doc.file_path == "/tmp/test.pdf"
    assert doc.mime_type == "application/pdf"

def test_document_storage_service_get_document_by_id(document_storage_service):
    doc = document_storage_service.create_document(
        title="Test Doc 2",
        content="Another test",
        file_path="/tmp/test2.pdf",
        mime_type="application/pdf"
    )
    retrieved = document_storage_service.get_document_by_id(doc.id)
    assert retrieved is not None
    assert retrieved.id == doc.id
    assert retrieved.title == "Test Doc 2"

def test_document_storage_service_list_documents(document_storage_service):
    document_storage_service.create_document(
        title="Doc A",
        content="Content A",
        file_path="/tmp/a.pdf",
        mime_type="application/pdf"
    )
    document_storage_service.create_document(
        title="Doc B",
        content="Content B",
        file_path="/tmp/b.pdf",
        mime_type="application/pdf"
    )
    docs = document_storage_service.list_documents()
    assert len(docs) == 2
    assert any(d.title == "Doc A" for d in docs)
    assert any(d.title == "Doc B" for d in docs)

def test_document_storage_service_delete_document(document_storage_service):
    doc = document_storage_service.create_document(
        title="To Delete",
        content="Will be deleted",
        file_path="/tmp/delete.pdf",
        mime_type="application/pdf"
    )
    success = document_storage_service.delete_document(doc.id)
    assert success is True
    assert document_storage_service.get_document_by_id(doc.id) is None