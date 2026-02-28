from fastapi.testclient import TestClient
from app.main import app
from app.services.documentpreviewservice import DocumentPreviewService
from unittest.mock import patch, MagicMock
import pytest

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_document_preview_service():
    with patch('app.services.documentpreviewservice.DocumentPreviewService') as mock:
        yield mock

def test_get_document_preview_success(client, mock_document_preview_service):
    mock_instance = MagicMock()
    mock_instance.get_preview.return_value = {"content": "preview_data", "mime_type": "text/plain"}
    mock_document_preview_service.return_value = mock_instance
    response = client.get("/api/v1/documents/123/preview")
    assert response.status_code == 200
    assert response.json() == {"content": "preview_data", "mime_type": "text/plain"}

def test_get_document_preview_not_found(client, mock_document_preview_service):
    mock_instance = MagicMock()
    mock_instance.get_preview.side_effect = ValueError("Document not found")
    mock_document_preview_service.return_value = mock_instance
    response = client.get("/api/v1/documents/999/preview")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"

def test_get_document_preview_internal_error(client, mock_document_preview_service):
    mock_instance = MagicMock()
    mock_instance.get_preview.side_effect = Exception("Unexpected error")
    mock_document_preview_service.return_value = mock_instance
    response = client.get("/api/v1/documents/123/preview")
    assert response.status_code == 500
    assert "detail" in response.json()