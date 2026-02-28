import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.models import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    with patch("app.main.get_db", return_value=db_session):
        with TestClient(app) as c:
            yield c

@pytest.fixture(scope="function")
def mock_document_storage_service():
    with patch("app.services.documentstorageservice.DocumentStorageService") as mock:
        yield mock

@pytest.fixture(scope="function")
def mock_document_preview_service():
    with patch("app.services.documentpreviewservice.DocumentPreviewService") as mock:
        yield mock

def test_get_document_by_id_success(client, db_session, mock_document_storage_service, mock_document_preview_service):
    doc = Document(id=1, title="Test Doc", content="test content", file_path="/path/to/doc.pdf", mime_type="application/pdf")
    db_session.add(doc)
    db_session.commit()
    mock_document_storage_service.return_value.get_document_metadata.return_value = {"size": 1024, "last_modified": "2023-01-01T00:00:00Z"}
    mock_document_preview_service.return_value.generate_preview_url.return_value = "https://preview.example.com/1"
    response = client.get("/api/v1/documents/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Test Doc"
    assert data["preview_url"] == "https://preview.example.com/1"
    assert data["metadata"]["size"] == 1024

def test_get_document_by_id_not_found(client):
    response = client.get("/api/v1/documents/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"

def test_get_document_by_id_invalid_id(client):
    response = client.get("/api/v1/documents/invalid")
    assert response.status_code == 422