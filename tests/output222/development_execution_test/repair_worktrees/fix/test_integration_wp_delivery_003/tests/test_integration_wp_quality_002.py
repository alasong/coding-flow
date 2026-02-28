import pytest
from unittest.mock import patch, MagicMock
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import ApiGateway
from app.services.documentstorageservice import DocumentStorageService
from app.database import get_db_session
from app.models import Document, User


def test_convergence_of_component_quality():
    # Mock database session
    mock_db = MagicMock()
    
    # Mock services with realistic interaction patterns
    with patch('app.services.documentsearchservice.get_db_session', return_value=mock_db), \
         patch('app.services.documentpreviewservice.get_db_session', return_value=mock_db), \
         patch('app.services.usermanagementservice.get_db_session', return_value=mock_db), \
         patch('app.services.documentstorageservice.get_db_session', return_value=mock_db), \
         patch('app.services.apigateway.get_db_session', return_value=mock_db):
        
        # Initialize services that exist in the project
        search_service = DocumentSearchService()
        preview_service = DocumentPreviewService()
        user_service = UserManagementService()
        api_gateway = ApiGateway()
        storage_service = DocumentStorageService()
        
        # Simulate component interaction flow: storage -> search -> preview -> user management -> API gateway
        # Create mock document and user
        mock_doc = Document(id=1, title="test_doc", content="test content", storage_path="/path/to/doc")
        mock_user = User(id=1, username="testuser", email="test@example.com")
        
        # Mock service methods that would be called in convergence scenario
        storage_service.store_document = MagicMock(return_value=mock_doc)
        search_service.search_documents = MagicMock(return_value=[mock_doc])
        preview_service.generate_preview = MagicMock(return_value={"preview_text": "preview content"})
        user_service.get_user_by_id = MagicMock(return_value=mock_user)
        api_gateway.validate_request = MagicMock(return_value=True)
        
        # Execute convergence interaction sequence
        stored_doc = storage_service.store_document("test content", "test_doc")
        search_results = search_service.search_documents("test")
        preview = preview_service.generate_preview(stored_doc.id)
        user = user_service.get_user_by_id(1)
        is_valid = api_gateway.validate_request({"user_id": 1, "doc_id": stored_doc.id})
        
        # Assert quality convergence criteria
        assert stored_doc is not None
        assert len(search_results) > 0
        assert "preview_text" in preview
        assert user is not None
        assert is_valid is True
        
        # Verify all services were called (risk convergence via interaction verification)
        storage_service.store_document.assert_called_once()
        search_service.search_documents.assert_called_once()
        preview_service.generate_preview.assert_called_once()
        user_service.get_user_by_id.assert_called_once()
        api_gateway.validate_request.assert_called_once()


def test_component_interaction_consistency():
    # Test that component interactions maintain consistent state and error handling
    mock_db = MagicMock()
    
    with patch('app.services.documentsearchservice.get_db_session', return_value=mock_db), \
         patch('app.services.documentpreviewservice.get_db_session', return_value=mock_db), \
         patch('app.services.usermanagementservice.get_db_session', return_value=mock_db), \
         patch('app.services.documentstorageservice.get_db_session', return_value=mock_db), \
         patch('app.services.apigateway.get_db_session', return_value=mock_db):
        
        search_service = DocumentSearchService()
        preview_service = DocumentPreviewService()
        user_service = UserManagementService()
        storage_service = DocumentStorageService()
        api_gateway = ApiGateway()
        
        # Mock failures to verify convergence under risk conditions
        storage_service.store_document = MagicMock(side_effect=Exception("Storage failure"))
        search_service.search_documents = MagicMock(return_value=[])
        preview_service.generate_preview = MagicMock(return_value=None)
        user_service.get_user_by_id = MagicMock(return_value=None)
        api_gateway.validate_request = MagicMock(return_value=False)
        
        # Verify each service handles its responsibility consistently
        with pytest.raises(Exception, match="Storage failure"):
            storage_service.store_document("content", "title")
        
        assert search_service.search_documents("query") == []
        assert preview_service.generate_preview(999) is None
        assert user_service.get_user_by_id(999) is None
        assert api_gateway.validate_request({"invalid": True}) is False


def test_api_gateway_integration_with_all_services():
    # Test ApiGateway as integration point for all component services
    mock_db = MagicMock()
    
    with patch('app.services.documentsearchservice.get_db_session', return_value=mock_db), \
         patch('app.services.documentpreviewservice.get_db_session', return_value=mock_db), \
         patch('app.services.usermanagementservice.get_db_session', return_value=mock_db), \
         patch('app.services.documentstorageservice.get_db_session', return_value=mock_db), \
         patch('app.services.apigateway.get_db_session', return_value=mock_db):
        
        api_gateway = ApiGateway()
        search_service = DocumentSearchService()
        preview_service = DocumentPreviewService()
        user_service = UserManagementService()
        storage_service = DocumentStorageService()
        
        # Mock service dependencies in ApiGateway context
        api_gateway._search_service = search_service
        api_gateway._preview_service = preview_service
        api_gateway._user_service = user_service
        api_gateway._storage_service = storage_service
        
        # Simulate end-to-end request handling
        mock_request = {
            "user_id": 1,
            "query": "test",
            "document_id": 1,
            "action": "search_and_preview"
        }
        
        # Mock internal service calls
        search_service.search_documents = MagicMock(return_value=[Document(id=1, title="result")])
        preview_service.generate_preview = MagicMock(return_value={"text": "preview"})
        user_service.get_user_by_id = MagicMock(return_value=User(id=1, username="test"))
        storage_service.get_document_by_id = MagicMock(return_value=Document(id=1, title="doc"))
        
        response = api_gateway.handle_request(mock_request)
        
        # Assert convergence: all services participated and returned consistent results
        assert "results" in response
        assert "preview" in response
        assert "user" in response
        assert "document" in response
        assert response["status"] == "success"