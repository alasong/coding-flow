import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentsearchservice import DocumentSearchService
from app.models import Document

client = TestClient(app)

@pytest.fixture
def mock_document_storage_service(mocker):
    return mocker.patch('app.services.documentstorageservice.DocumentStorageService')

@pytest.fixture
def mock_document_preview_service(mocker):
    return mocker.patch('app.services.documentpreviewservice.DocumentPreviewService')

@pytest.fixture
def mock_document_search_service(mocker):
    return mocker.patch('app.services.documentsearchservice.DocumentSearchService')

def test_get_document_by_id_success(mock_document_storage_service, mock_document_preview_service, mock_document_search_service):
    doc_id = "doc-123"
    mock_doc = Document(id=doc_id, title="Test Doc", content="content", mime_type="text/plain")
    mock_document_storage_service.get_document_by_id.return_value = mock_doc
    mock_document_preview_service.generate_preview.return_value = "preview-data"
    mock_document_search_service.get_document_metadata.return_value = {"size": 1024, "created_at": "2023-01-01T00:00:00"}

    response = client.get(f"/api/v1/documents/{doc_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["title"] == "Test Doc"
    assert "preview" in data
    assert "metadata" in data
    assert data["metadata"]["size"] == 1024

def test_get_document_by_id_not_found(mock_document_storage_service, mock_document_preview_service, mock_document_search_service):
    doc_id = "nonexistent"
    mock_document_storage_service.get_document_by_id.return_value = None

    response = client.get(f"/api/v1/documents/{doc_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"

def test_get_document_by_id_storage_error(mock_document_storage_service, mock_document_preview_service, mock_document_search_service):
    doc_id = "doc-err"
    mock_document_storage_service.get_document_by_id.side_effect = Exception("Storage failure")

    response = client.get(f"/api/v1/documents/{doc_id}")

    assert response.status_code == 500
    assert "detail" in response.json()

def test_get_document_by_id_interactive_services_integration(mock_document_storage_service, mock_document_preview_service, mock_document_search_service):
    doc_id = "integrated-doc"
    mock_doc = Document(id=doc_id, title="Integrated Test", content="test content", mime_type="application/pdf")
    mock_document_storage_service.get_document_by_id.return_value = mock_doc
    mock_document_preview_service.generate_preview.return_value = "base64-preview"
    mock_document_search_service.get_document_metadata.return_value = {"size": 2048, "created_at": "2023-02-01T12:00:00"}

    response = client.get(f"/api/v1/documents/{doc_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["preview"] == "base64-preview"
    assert data["metadata"]["size"] == 2048
    assert "created_at" in data["metadata"]