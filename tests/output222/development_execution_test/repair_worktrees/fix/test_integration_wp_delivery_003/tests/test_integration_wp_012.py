import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import DocumentCreate
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentsearchservice import DocumentSearchService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import ApiGateway

client = TestClient(app)

@pytest.fixture
def mock_document_storage_service(mocker):
    return mocker.patch('app.main.DocumentStorageService')

@pytest.fixture
def mock_document_preview_service(mocker):
    return mocker.patch('app.main.DocumentPreviewService')

@pytest.fixture
def mock_document_search_service(mocker):
    return mocker.patch('app.main.DocumentSearchService')

@pytest.fixture
def mock_user_management_service(mocker):
    return mocker.patch('app.main.UserManagementService')

@pytest.fixture
def mock_api_gateway(mocker):
    return mocker.patch('app.main.ApiGateway')

def test_post_documents_success(
    mock_document_storage_service,
    mock_document_preview_service,
    mock_document_search_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    mock_document_storage_service.return_value.store_document.return_value = "doc-123"
    mock_document_preview_service.return_value.generate_preview.return_value = True
    mock_document_search_service.return_value.index_document.return_value = True
    mock_user_management_service.return_value.get_current_user.return_value = {"id": "user-456", "role": "admin"}
    mock_api_gateway.return_value.validate_request.return_value = True
    
    document_data = {
        "title": "Test Document",
        "content": "This is a test document content.",
        "file_type": "text/plain",
        "tags": ["test", "integration"]
    }
    
    # Act
    response = client.post("/api/v1/documents", json=document_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["id"] == "doc-123"
    assert response.json()["title"] == "Test Document"
    mock_document_storage_service.return_value.store_document.assert_called_once()
    mock_document_preview_service.return_value.generate_preview.assert_called_once()
    mock_document_search_service.return_value.index_document.assert_called_once()
    mock_user_management_service.return_value.get_current_user.assert_called_once()
    mock_api_gateway.return_value.validate_request.assert_called_once()

def test_post_documents_validation_error(mock_api_gateway):
    # Arrange
    mock_api_gateway.return_value.validate_request.return_value = False
    
    # Act
    response = client.post("/api/v1/documents", json={})
    
    # Assert
    assert response.status_code == 400
    assert "validation" in response.json()["detail"].lower()

def test_post_documents_storage_failure(
    mock_document_storage_service,
    mock_api_gateway,
    mock_user_management_service
):
    # Arrange
    mock_api_gateway.return_value.validate_request.return_value = True
    mock_user_management_service.return_value.get_current_user.return_value = {"id": "user-456", "role": "admin"}
    mock_document_storage_service.return_value.store_document.side_effect = Exception("Storage failed")
    
    # Act
    response = client.post("/api/v1/documents", json={
        "title": "Test",
        "content": "content",
        "file_type": "text/plain"
    })
    
    # Assert
    assert response.status_code == 500
    assert "storage" in response.json()["detail"].lower()

def test_post_documents_dependency_interaction(
    mock_document_storage_service,
    mock_document_preview_service,
    mock_document_search_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    mock_api_gateway.return_value.validate_request.return_value = True
    mock_user_management_service.return_value.get_current_user.return_value = {"id": "user-456", "role": "admin"}
    mock_document_storage_service.return_value.store_document.return_value = "doc-789"
    mock_document_preview_service.return_value.generate_preview.return_value = True
    mock_document_search_service.return_value.index_document.return_value = True
    
    # Act
    response = client.post("/api/v1/documents", json={
        "title": "Dependency Test",
        "content": "Testing service interactions",
        "file_type": "application/pdf",
        "tags": ["dependency", "test"]
    })
    
    # Assert
    assert response.status_code == 201
    assert response.json()["id"] == "doc-789"
    mock_document_storage_service.return_value.store_document.assert_called_once()
    mock_document_preview_service.return_value.generate_preview.assert_called_once_with("doc-789")
    mock_document_search_service.return_value.index_document.assert_called_once_with("doc-789")