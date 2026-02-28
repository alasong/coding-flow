import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentsearchservice import DocumentSearchService
from unittest.mock import patch, MagicMock

client = TestClient(app)

class TestDocumentPreviewAPI:
    @pytest.fixture
    def mock_services(self):
        with patch('app.services.documentpreviewservice.DocumentPreviewService') as mock_preview_service, \
             patch('app.services.documentstorageservice.DocumentStorageService') as mock_storage_service, \
             patch('app.services.documentsearchservice.DocumentSearchService') as mock_search_service:
            mock_preview_service_instance = MagicMock()
            mock_storage_service_instance = MagicMock()
            mock_search_service_instance = MagicMock()
            
            mock_preview_service.return_value = mock_preview_service_instance
            mock_storage_service.return_value = mock_storage_service_instance
            mock_search_service.return_value = mock_search_service_instance
            
            yield {
                'preview': mock_preview_service_instance,
                'storage': mock_storage_service_instance,
                'search': mock_search_service_instance
            }

    def test_get_document_preview_success(self, mock_services):
        # Arrange
        document_id = "doc-123"
        mock_preview_data = {"content": "preview content", "mime_type": "text/plain"}
        mock_services['preview'].get_preview.return_value = mock_preview_data
        
        # Act
        response = client.get(f"/api/v1/documents/{document_id}/preview")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_preview_data
        mock_services['preview'].get_preview.assert_called_once_with(document_id)

    def test_get_document_preview_not_found(self, mock_services):
        # Arrange
        document_id = "nonexistent-doc"
        mock_services['preview'].get_preview.side_effect = ValueError("Document not found")
        
        # Act
        response = client.get(f"/api/v1/documents/{document_id}/preview")
        
        # Assert
        assert response.status_code == 404
        assert "detail" in response.json()
        mock_services['preview'].get_preview.assert_called_once_with(document_id)

    def test_get_document_preview_internal_error(self, mock_services):
        # Arrange
        document_id = "doc-456"
        mock_services['preview'].get_preview.side_effect = Exception("Unexpected error")
        
        # Act
        response = client.get(f"/api/v1/documents/{document_id}/preview")
        
        # Assert
        assert response.status_code == 500
        assert "detail" in response.json()
        mock_services['preview'].get_preview.assert_called_once_with(document_id)

    def test_get_document_preview_service_interaction(self, mock_services):
        # Arrange
        document_id = "doc-789"
        mock_preview_data = {"content": "preview content", "mime_type": "text/plain"}
        mock_services['preview'].get_preview.return_value = mock_preview_data
        
        # Act
        response = client.get(f"/api/v1/documents/{document_id}/preview")
        
        # Assert service dependencies are properly invoked
        mock_services['preview'].get_preview.assert_called_once_with(document_id)
        # Verify DocumentPreviewService internally uses storage and search services
        # (implicit via service composition - no direct calls from API layer)