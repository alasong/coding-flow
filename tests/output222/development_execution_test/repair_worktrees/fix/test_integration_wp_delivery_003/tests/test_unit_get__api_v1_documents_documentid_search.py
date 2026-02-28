import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.documentsearchservice import DocumentSearchService
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_document_search_service():
    with patch('app.services.documentsearchservice.DocumentSearchService') as mock:
        yield mock

def test_get_document_search_success(client, mock_document_search_service):
    mock_instance = mock_document_search_service.return_value
    mock_instance.search_in_document.return_value = {"results": [{"id": "1", "text": "match"}]}
    response = client.get("/api/v1/documents/123/search?q=test")
    assert response.status_code == 200
    assert response.json() == {"results": [{"id": "1", "text": "match"}]}

def test_get_document_search_document_not_found(client, mock_document_search_service):
    mock_instance = mock_document_search_service.return_value
    mock_instance.search_in_document.side_effect = ValueError("Document not found")
    response = client.get("/api/v1/documents/999/search?q=test")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"

def test_get_document_search_invalid_query(client):
    response = client.get("/api/v1/documents/123/search")
    assert response.status_code == 422

def test_get_document_search_service_error(client, mock_document_search_service):
    mock_instance = mock_document_search_service.return_value
    mock_instance.search_in_document.side_effect = Exception("Internal error")
    response = client.get("/api/v1/documents/123/search?q=test")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal error"