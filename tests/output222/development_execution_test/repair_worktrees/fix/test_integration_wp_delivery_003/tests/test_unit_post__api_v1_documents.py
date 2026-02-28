import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Document
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService

@pytest.fixture(scope="function")
def test_client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
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

def test_post_documents_success(test_client, db_session, monkeypatch):
    def mock_store_document(*args, **kwargs):
        return {"id": "doc_123", "name": "test.pdf", "size": 1024}
    def mock_index_document(*args, **kwargs):
        return True
    def mock_generate_preview(*args, **kwargs):
        return {"preview_id": "prev_456"}
    monkeypatch.setattr(DocumentStorageService, "store_document", mock_store_document)
    monkeypatch.setattr(DocumentSearchService, "index_document", mock_index_document)
    monkeypatch.setattr(DocumentPreviewService, "generate_preview", mock_generate_preview)
    
    response = test_client.post(
        "/api/v1/documents",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
        data={"metadata": '{"title": "Test Doc", "tags": ["test"]}'}
    )
    assert response.status_code == 201
    assert response.json()["id"] == "doc_123"
    assert response.json()["name"] == "test.pdf"

def test_post_documents_no_file(test_client):
    response = test_client.post("/api/v1/documents", data={"metadata": '{"title": "Test"}'})
    assert response.status_code == 422

def test_post_documents_invalid_metadata(test_client):
    response = test_client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", b"content", "text/plain")},
        data={"metadata": "invalid json"}
    )
    assert response.status_code == 422

def test_post_documents_storage_failure(test_client, monkeypatch):
    def mock_store_document(*args, **kwargs):
        raise Exception("Storage failed")
    monkeypatch.setattr(DocumentStorageService, "store_document", mock_store_document)
    
    response = test_client.post(
        "/api/v1/documents",
        files={"file": ("test.pdf", b"content", "application/pdf")},
        data={"metadata": '{"title": "Test"}'}
    )
    assert response.status_code == 500
    assert "Storage failed" in response.json()["detail"]