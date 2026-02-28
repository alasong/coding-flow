import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import ApiGateway

client = TestClient(app)

@pytest.fixture
def mock_document_storage_service(mocker):
    return mocker.patch('app.main.DocumentStorageService', autospec=True)

@pytest.fixture
def mock_document_search_service(mocker):
    return mocker.patch('app.main.DocumentSearchService', autospec=True)

@pytest.fixture
def mock_document_preview_service(mocker):
    return mocker.patch('app.main.DocumentPreviewService', autospec=True)

@pytest.fixture
def mock_user_management_service(mocker):
    return mocker.patch('app.main.UserManagementService', autospec=True)

@pytest.fixture
def mock_api_gateway(mocker):
    return mocker.patch('app.main.ApiGateway', autospec=True)

def test_get_document_versions_success(
    mock_document_storage_service,
    mock_document_search_service,
    mock_document_preview_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    document_id = "doc-123"
    mock_storage = DocumentStorageService()
    mock_storage.get_document_versions.return_value = [
        {"version_id": "v1", "created_at": "2023-01-01T00:00:00Z", "size": 1024},
        {"version_id": "v2", "created_at": "2023-01-02T00:00:00Z", "size": 2048}
    ]
    
    # Patch the instance method on the service class used in main.py
    mock_document_storage_service.return_value = mock_storage
    
    # Act
    response = client.get(f"/api/v1/documents/{document_id}/versions")
    
    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["version_id"] == "v1"
    assert response.json()[1]["version_id"] == "v2"

def test_get_document_versions_not_found(
    mock_document_storage_service,
    mock_document_search_service,
    mock_document_preview_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    document_id = "nonexistent-doc"
    mock_storage = DocumentStorageService()
    mock_storage.get_document_versions.return_value = []
    mock_document_storage_service.return_value = mock_storage
    
    # Act
    response = client.get(f"/api/v1/documents/{document_id}/versions")
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found or no versions available"

def test_get_document_versions_service_dependency_interactions(
    mock_document_storage_service,
    mock_document_search_service,
    mock_document_preview_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    document_id = "doc-456"
    mock_storage = DocumentStorageService()
    mock_storage.get_document_versions.return_value = [{"version_id": "v1"}]
    mock_document_storage_service.return_value = mock_storage
    
    # Act
    response = client.get(f"/api/v1/documents/{document_id}/versions")
    
    # Assert service dependencies were invoked as expected
    mock_document_storage_service.assert_called_once()
    mock_document_search_service.assert_not_called()
    mock_document_preview_service.assert_not_called()
    mock_user_management_service.assert_not_called()
    mock_api_gateway.assert_not_called()
    assert response.status_code == 200