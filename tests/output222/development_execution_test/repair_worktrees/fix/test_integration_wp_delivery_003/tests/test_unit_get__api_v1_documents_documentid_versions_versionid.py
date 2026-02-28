import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.models import Document, DocumentVersion
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_document_storage_service():
    with patch('app.services.documentstorageservice.DocumentStorageService') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_document_search_service():
    with patch('app.services.documentsearchservice.DocumentSearchService') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

def test_get_document_version_success(client, db_session, mock_document_storage_service, mock_document_search_service):
    doc = Document(id="doc-001", title="Test Doc", content="content", created_by="user-001")
    db_session.add(doc)
    db_session.flush()
    version = DocumentVersion(
        id="ver-001",
        document_id="doc-001",
        version_number=1,
        content_hash="abc123",
        storage_key="docs/doc-001/v1.json",
        created_at="2023-01-01T00:00:00"
    )
    db_session.add(version)
    db_session.commit()

    response = client.get("/api/v1/documents/doc-001/versions/ver-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ver-001"
    assert data["document_id"] == "doc-001"
    assert data["version_number"] == 1

def test_get_document_version_not_found(client, db_session, mock_document_storage_service, mock_document_search_service):
    response = client.get("/api/v1/documents/nonexistent/versions/ver-001")
    assert response.status_code == 404

def test_get_document_version_version_not_found(client, db_session, mock_document_storage_service, mock_document_search_service):
    doc = Document(id="doc-001", title="Test Doc", content="content", created_by="user-001")
    db_session.add(doc)
    db_session.commit()

    response = client.get("/api/v1/documents/doc-001/versions/nonexistent")
    assert response.status_code == 404