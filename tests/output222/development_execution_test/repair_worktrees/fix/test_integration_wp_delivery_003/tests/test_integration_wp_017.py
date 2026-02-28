import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentsearchservice import DocumentSearchService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import ApiGateway

client = TestClient(app)

@pytest.fixture
def mock_document_storage_service(mocker):
    return mocker.patch('app.main.DocumentStorageService', autospec=True)

@pytest.fixture
def mock_document_preview_service(mocker):
    return mocker.patch('app.main.DocumentPreviewService', autospec=True)

@pytest.fixture
def mock_document_search_service(mocker):
    return mocker.patch('app.main.DocumentSearchService', autospec=True)

@pytest.fixture
def mock_user_management_service(mocker):
    return mocker.patch('app.main.UserManagementService', autospec=True)

@pytest.fixture
def mock_api_gateway(mocker):
    return mocker.patch('app.main.ApiGateway', autospec=True)

def test_get_document_version_success(
    mock_document_storage_service,
    mock_document_preview_service,
    mock_document_search_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    document_id = "doc-123"
    version_id = "v1.0.0"
    expected_response = {
        "documentId": document_id,
        "versionId": version_id,
        "content": "test content",
        "metadata": {"size": 1024}
    }
    
    mock_document_storage_service.return_value.get_version.return_value = expected_response
    
    # Act
    response = client.get(f"/api/v1/documents/{document_id}/versions/{version_id}")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == expected_response
    mock_document_storage_service.return_value.get_version.assert_called_once_with(document_id, version_id)
    mock_document_preview_service.return_value.get_preview_metadata.assert_not_called()
    mock_document_search_service.return_value.search_by_document_id.assert_not_called()
    mock_user_management_service.return_value.validate_user_access.assert_called_once()
    mock_api_gateway.return_value.log_api_call.assert_called_once()

def test_get_document_version_not_found(
    mock_document_storage_service,
    mock_document_preview_service,
    mock_document_search_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    document_id = "doc-456"
    version_id = "v2.0.0"
    
    mock_document_storage_service.return_value.get_version.side_effect = KeyError("Version not found")
    
    # Act
    response = client.get(f"/api/v1/documents/{document_id}/versions/{version_id}")
    
    # Assert
    assert response.status_code == 404
    assert "detail" in response.json()
    mock_document_storage_service.return_value.get_version.assert_called_once_with(document_id, version_id)

def test_get_document_version_internal_error(
    mock_document_storage_service,
    mock_document_preview_service,
    mock_document_search_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    document_id = "doc-789"
    version_id = "v3.0.0"
    
    mock_document_storage_service.return_value.get_version.side_effect = Exception("Database connection failed")
    
    # Act
    response = client.get(f"/api/v1/documents/{document_id}/versions/{version_id}")
    
    # Assert
    assert response.status_code == 500
    assert "detail" in response.json()
    mock_document_storage_service.return_value.get_version.assert_called_once_with(document_id, version_id)

def test_get_document_version_service_interactions(
    mock_document_storage_service,
    mock_document_preview_service,
    mock_document_search_service,
    mock_user_management_service,
    mock_api_gateway
):
    # Arrange
    document_id = "doc-abc"
    version_id = "v1.2.3"
    expected_response = {
        "documentId": document_id,
        "versionId": version_id,
        "content": "test content",
        "metadata": {"size": 2048}
    }
    
    mock_document_storage_service.return_value.get_version.return_value = expected_response
    
    # Act
    response = client.get(f"/api/v1/documents/{document_id}/versions/{version_id}")
    
    # Assert
    assert response.status_code == 200
    
    # Verify service interactions
    mock_document_storage_service.assert_called_once()
    mock_document_preview_service.assert_called_once()
    mock_document_search_service.assert_called_once()
    mock_user_management_service.assert_called_once()
    mock_api_gateway.assert_called_once()
    
    # Verify dependency call order and parameters
    mock_user_management_service.return_value.validate_user_access.assert_called_with(document_id)
    mock_document_storage_service.return_value.get_version.assert_called_with(document_id, version_id)
    mock_api_gateway.return_value.log_api_call.assert_called_with(
        "GET", 
        f"/api/v1/documents/{document_id}/versions/{version_id}",
        200
    )