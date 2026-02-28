import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import ApiGateway

client = TestClient(app)

@pytest.fixture
def mock_document_search_service(mocker):
    return mocker.patch('app.main.DocumentSearchService')

@pytest.fixture
def mock_document_storage_service(mocker):
    return mocker.patch('app.main.DocumentStorageService')

@pytest.fixture
def mock_document_preview_service(mocker):
    return mocker.patch('app.main.DocumentPreviewService')

@pytest.fixture
def mock_user_management_service(mocker):
    return mocker.patch('app.main.UserManagementService')

@pytest.fixture
def mock_api_gateway(mocker):
    return mocker.patch('app.main.ApiGateway')

def test_get_document_search_success(
    mock_document_search_service,
    mock_document_storage_service,
    mock_document_preview_service,
    mock_user_management_service,
    mock_api_gateway
):
    mock_document_search_service.return_value.search_document.return_value = {
        "results": [{"id": "result-1", "score": 0.95, "snippet": "sample snippet"}],
        "total": 1
    }
    mock_document_storage_service.return_value.get_document_metadata.return_value = {"id": "doc-123", "title": "Test Doc"}
    mock_user_management_service.return_value.validate_user_access.return_value = True
    mock_api_gateway.return_value.log_api_call.return_value = None

    response = client.get("/api/v1/documents/doc-123/search?q=test&limit=10&offset=0")
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "result-1"

def test_get_document_search_document_not_found(
    mock_document_search_service,
    mock_document_storage_service,
    mock_user_management_service,
    mock_api_gateway
):
    mock_document_storage_service.return_value.get_document_metadata.side_effect = ValueError("Document not found")
    mock_user_management_service.return_value.validate_user_access.return_value = True
    mock_api_gateway.return_value.log_api_call.return_value = None

    response = client.get("/api/v1/documents/invalid-doc-id/search?q=test")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"

def test_get_document_search_unauthorized(
    mock_document_storage_service,
    mock_user_management_service,
    mock_api_gateway
):
    mock_document_storage_service.return_value.get_document_metadata.return_value = {"id": "doc-123", "title": "Test Doc"}
    mock_user_management_service.return_value.validate_user_access.return_value = False
    mock_api_gateway.return_value.log_api_call.return_value = None

    response = client.get("/api/v1/documents/doc-123/search?q=test")
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"

def test_get_document_search_validation_error(
    mock_document_storage_service,
    mock_user_management_service,
    mock_api_gateway
):
    mock_document_storage_service.return_value.get_document_metadata.return_value = {"id": "doc-123", "title": "Test Doc"}
    mock_user_management_service.return_value.validate_user_access.return_value = True
    mock_api_gateway.return_value.log_api_call.return_value = None

    response = client.get("/api/v1/documents/doc-123/search?q=")
    
    assert response.status_code == 422

def test_get_document_search_service_integration(
    mock_document_search_service,
    mock_document_storage_service,
    mock_document_preview_service,
    mock_user_management_service,
    mock_api_gateway
):
    mock_document_storage_service.return_value.get_document_metadata.return_value = {"id": "doc-123", "title": "Test Doc", "content_type": "text/plain"}
    mock_user_management_service.return_value.validate_user_access.return_value = True
    mock_api_gateway.return_value.log_api_call.return_value = None
    mock_document_search_service.return_value.search_document.return_value = {
        "results": [{"id": "result-1", "score": 0.95, "snippet": "sample snippet"}],
        "total": 1
    }
    mock_document_preview_service.return_value.generate_preview.return_value = "preview-content"

    response = client.get("/api/v1/documents/doc-123/search?q=test&with_preview=true")
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "preview" in data["results"][0]