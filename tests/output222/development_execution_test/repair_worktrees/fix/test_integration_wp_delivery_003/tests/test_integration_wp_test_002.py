import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagementService
from app.services.documentstorageservice import DocumentStorageService
from app.services.apigateway import ApiGateway
from app.database import get_db
from unittest.mock import patch, MagicMock

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_services():
    with patch('app.main.DocumentSearchService') as mock_search, \
         patch('app.main.DocumentPreviewService') as mock_preview, \
         patch('app.main.UserManagementService') as mock_user, \
         patch('app.main.DocumentStorageService') as mock_storage, \
         patch('app.main.ApiGateway') as mock_api_gateway:
        mock_search.return_value = MagicMock()
        mock_preview.return_value = MagicMock()
        mock_user.return_value = MagicMock()
        mock_storage.return_value = MagicMock()
        mock_api_gateway.return_value = MagicMock()
        yield {
            'search': mock_search.return_value,
            'preview': mock_preview.return_value,
            'user': mock_user.return_value,
            'storage': mock_storage.return_value,
            'api_gateway': mock_api_gateway.return_value
        }

def test_end_to_end_document_search_and_preview_flow(test_client, mock_services):
    # Simulate user authentication flow
    mock_services['user'].authenticate_user.return_value = {"user_id": "test-user-123", "role": "admin"}
    
    # Simulate document storage and search flow
    mock_services['storage'].store_document.return_value = "doc-abc123"
    mock_services['search'].search_documents.return_value = [{"id": "doc-abc123", "title": "Test Doc"}]
    mock_services['preview'].get_preview.return_value = b"%PDF-1.4..."
    
    # Perform end-to-end flow: auth -> store -> search -> preview
    # Step 1: Authenticate user
    auth_response = test_client.post("/api/v1/auth/login", json={"username": "test", "password": "pass"})
    assert auth_response.status_code == 200
    
    # Step 2: Store document (via API gateway)
    mock_services['api_gateway'].handle_request.return_value = {"status": "success", "document_id": "doc-abc123"}
    store_response = test_client.post("/api/v1/documents", 
                                    json={"title": "Test Doc", "content": "test content"},
                                    headers={"Authorization": "Bearer test-token"})
    assert store_response.status_code == 200
    
    # Step 3: Search for document
    search_response = test_client.get("/api/v1/documents/search?q=test", 
                                     headers={"Authorization": "Bearer test-token"})
    assert search_response.status_code == 200
    assert len(search_response.json()) > 0
    assert search_response.json()[0]["id"] == "doc-abc123"
    
    # Step 4: Retrieve preview
    preview_response = test_client.get("/api/v1/documents/doc-abc123/preview",
                                     headers={"Authorization": "Bearer test-token"})
    assert preview_response.status_code == 200
    assert preview_response.headers["content-type"] == "application/pdf"

def test_end_to_end_user_management_document_flow(test_client, mock_services):
    # Setup mocks for user and document interaction
    mock_services['user'].create_user.return_value = {"user_id": "new-user-456", "email": "test@example.com"}
    mock_services['user'].get_user_by_email.return_value = {"user_id": "new-user-456", "email": "test@example.com"}
    mock_services['storage'].list_user_documents.return_value = [{"id": "doc-789", "title": "User Doc"}]
    
    # Create user
    create_user_response = test_client.post("/api/v1/users", 
                                          json={"email": "test@example.com", "password": "secure123"})
    assert create_user_response.status_code == 200
    
    # Get user and list their documents
    user_response = test_client.get("/api/v1/users/test@example.com")
    assert user_response.status_code == 200
    assert user_response.json()["email"] == "test@example.com"
    
    docs_response = test_client.get("/api/v1/users/new-user-456/documents")
    assert docs_response.status_code == 200
    assert len(docs_response.json()) == 1
    assert docs_response.json()[0]["id"] == "doc-789"

def test_api_gateway_integration_with_all_services(test_client, mock_services):
    # Verify ApiGateway orchestrates all services correctly
    mock_services['api_gateway'].handle_request.side_effect = [
        {"status": "authenticated", "user": {"id": "u-1"}},
        {"status": "stored", "document_id": "d-1"},
        {"status": "searched", "results": [{"id": "d-1"}]},
        {"status": "previewed", "content_type": "application/pdf"}
    ]
    
    # Simulate full gateway flow
    gateway_response = test_client.post("/api/v1/gateway", 
                                       json={"action": "auth", "payload": {"user": "test"}})
    assert gateway_response.status_code == 200
    assert gateway_response.json()["status"] == "authenticated"
    
    gateway_response = test_client.post("/api/v1/gateway", 
                                       json={"action": "store", "payload": {"content": "test"}})
    assert gateway_response.status_code == 200
    assert gateway_response.json()["status"] == "stored"
    
    gateway_response = test_client.post("/api/v1/gateway", 
                                       json={"action": "search", "payload": {"query": "test"}})
    assert gateway_response.status_code == 200
    assert gateway_response.json()["status"] == "searched"
    
    gateway_response = test_client.post("/api/v1/gateway", 
                                       json={"action": "preview", "payload": {"document_id": "d-1"}})
    assert gateway_response.status_code == 200
    assert gateway_response.json()["status"] == "previewed"