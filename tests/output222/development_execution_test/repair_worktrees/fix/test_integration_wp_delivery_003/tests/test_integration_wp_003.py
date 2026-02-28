import pytest
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentstorageservice import DocumentStorageService
from app.services.usermanagementservice import UserManagerService
from app.database import get_db_session
from app.models import Document, User

class TestDocumentSearchServiceIntegration:
    def test_search_documents_with_preview_and_storage_dependencies(self, mocker):
        mock_db = mocker.patch('app.services.documentsearchservice.get_db_session')
        mock_storage = mocker.patch('app.services.documentsearchservice.DocumentStorageService')
        mock_preview = mocker.patch('app.services.documentsearchservice.DocumentPreviewService')
        mock_user_manager = mocker.patch('app.services.documentsearchservice.UserManagerService')
        
        # Mock database session and query results
        mock_session = mocker.Mock()
        mock_db.return_value.__enter__.return_value = mock_session
        mock_document = Document(id=1, title="Test Doc", content="test content", user_id=1)
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_document]
        
        # Mock dependencies' methods
        mock_storage_instance = mock_storage.return_value
        mock_storage_instance.get_document_by_id.return_value = mock_document
        
        mock_preview_instance = mock_preview.return_value
        mock_preview_instance.generate_preview.return_value = "preview_content"
        
        mock_user_manager_instance = mock_user_manager.return_value
        mock_user_manager_instance.get_user_by_id.return_value = User(id=1, username="testuser")
        
        # Initialize service and execute search
        service = DocumentSearchService()
        results = service.search_documents(query="test", user_id=1)
        
        # Verify interactions with dependencies
        mock_storage_instance.get_document_by_id.assert_called_once_with(1)
        mock_preview_instance.generate_preview.assert_called_once_with(mock_document)
        mock_user_manager_instance.get_user_by_id.assert_called_once_with(1)
        
        # Validate result structure and content
        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["title"] == "Test Doc"
        assert results[0]["preview"] == "preview_content"
        assert results[0]["username"] == "testuser"

    def test_search_documents_empty_results(self, mocker):
        mock_db = mocker.patch('app.services.documentsearchservice.get_db_session')
        mock_storage = mocker.patch('app.services.documentsearchservice.DocumentStorageService')
        mock_preview = mocker.patch('app.services.documentsearchservice.DocumentPreviewService')
        mock_user_manager = mocker.patch('app.services.documentsearchservice.UserManagerService')
        
        mock_session = mocker.Mock()
        mock_db.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        mock_storage_instance = mock_storage.return_value
        mock_preview_instance = mock_preview.return_value
        mock_user_manager_instance = mock_user_manager.return_value
        
        service = DocumentSearchService()
        results = service.search_documents(query="nonexistent", user_id=999)
        
        assert len(results) == 0
        mock_storage_instance.get_document_by_id.assert_not_called()
        mock_preview_instance.generate_preview.assert_not_called()
        mock_user_manager_instance.get_user_by_id.assert_not_called()

    def test_search_documents_with_user_permission_check(self, mocker):
        mock_db = mocker.patch('app.services.documentsearchservice.get_db_session')
        mock_user_manager = mocker.patch('app.services.documentsearchservice.UserManagerService')
        
        mock_session = mocker.Mock()
        mock_db.return_value.__enter__.return_value = mock_session
        mock_document = Document(id=2, title="Private Doc", content="private", user_id=42)
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_document]
        
        mock_user_manager_instance = mock_user_manager.return_value
        mock_user_manager_instance.get_user_by_id.return_value = User(id=42, username="owner")
        
        service = DocumentSearchService()
        results = service.search_documents(query="private", user_id=42)
        
        assert len(results) == 1
        assert results[0]["id"] == 2
        mock_user_manager_instance.get_user_by_id.assert_called_once_with(42)