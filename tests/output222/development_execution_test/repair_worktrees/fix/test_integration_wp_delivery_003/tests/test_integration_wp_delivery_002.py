import pytest
from unittest.mock import patch, MagicMock
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import ApiGateway

class TestDeliveryHandover:
    @pytest.fixture
    def setup_services(self):
        storage_service = DocumentStorageService()
        search_service = DocumentSearchService()
        preview_service = DocumentPreviewService()
        user_service = UserManagementService()
        api_gateway = ApiGateway()
        return storage_service, search_service, preview_service, user_service, api_gateway

    def test_all_documents_archived(self, setup_services):
        storage_service, search_service, preview_service, user_service, api_gateway = setup_services
        
        with patch.object(storage_service, 'list_documents') as mock_list, \
             patch.object(storage_service, 'archive_document') as mock_archive, \
             patch.object(search_service, 'index_document') as mock_index, \
             patch.object(preview_service, 'generate_preview') as mock_preview, \
             patch.object(user_service, 'get_active_users') as mock_users:
            
            mock_list.return_value = [
                {'id': 'doc-001', 'name': 'handover-report.pdf', 'status': 'pending'},
                {'id': 'doc-002', 'name': 'acceptance-criteria.docx', 'status': 'pending'},
                {'id': 'doc-003', 'name': 'signoff-form.pdf', 'status': 'pending'}
            ]
            mock_users.return_value = [{'id': 'user-001', 'role': 'delivery'}]
            
            # Simulate handover process
            for doc in mock_list.return_value:
                mock_preview.return_value = True
                mock_index.return_value = True
                mock_archive.return_value = True
            
            # Verify all documents are archived
            assert len(mock_list.return_value) == 3
            assert mock_archive.call_count == 3
            assert mock_index.call_count == 3
            assert mock_preview.call_count == 3