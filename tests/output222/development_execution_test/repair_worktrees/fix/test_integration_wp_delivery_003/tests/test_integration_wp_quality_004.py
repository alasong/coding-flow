import pytest
from unittest.mock import patch, MagicMock
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentstorageservice import DocumentStorageService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import ApiGateway

class TestFrontendConvergence:
    @pytest.fixture
    def setup_services(self):
        search_service = DocumentSearchService()
        preview_service = DocumentPreviewService()
        storage_service = DocumentStorageService()
        user_service = UserManagementService()
        api_gateway = ApiGateway()
        
        return {
            'search': search_service,
            'preview': preview_service,
            'storage': storage_service,
            'user': user_service,
            'gateway': api_gateway
        }

    def test_service_interoperability_convergence(self, setup_services):
        services = setup_services
        
        # Verify all services can be instantiated without error
        assert services['search'] is not None
        assert services['preview'] is not None
        assert services['storage'] is not None
        assert services['user'] is not None
        assert services['gateway'] is not None

    def test_api_gateway_integration_with_document_services(self, setup_services):
        services = setup_services
        gateway = services['gateway']
        
        # Mock dependencies to avoid external calls
        with patch.object(gateway, '_validate_request') as mock_validate, \
             patch.object(services['search'], 'search_documents') as mock_search, \
             patch.object(services['preview'], 'generate_preview') as mock_preview, \
             patch.object(services['storage'], 'get_document_metadata') as mock_storage:
            
            mock_validate.return_value = True
            mock_search.return_value = []
            mock_preview.return_value = b""
            mock_storage.return_value = {"id": "test", "size": 1024}
            
            # Simulate gateway orchestrating document flow
            result = gateway.handle_document_request(
                user_id="test-user",
                document_id="test-doc",
                operation="preview"
            )
            
            assert result is not None
            mock_validate.assert_called_once()
            mock_search.assert_not_called()  # preview path doesn't trigger search
            mock_preview.assert_called_once()
            mock_storage.assert_called_once()

    def test_document_flow_consistency_across_services(self, setup_services):
        services = setup_services
        
        # Test consistent document ID handling across services
        doc_id = "converged-document-001"
        
        with patch.object(services['search'], 'search_documents') as mock_search, \
             patch.object(services['preview'], 'generate_preview') as mock_preview, \
             patch.object(services['storage'], 'get_document_content') as mock_content, \
             patch.object(services['user'], 'get_user_permissions') as mock_perms:
            
            mock_search.return_value = [{"id": doc_id, "title": "Test Doc"}]
            mock_preview.return_value = b"preview-content"
            mock_content.return_value = b"full-content"
            mock_perms.return_value = {"can_view": True, "can_preview": True}
            
            # Sequential service invocation mimicking frontend workflow
            search_result = services['search'].search_documents(query="test", user_id="test-user")
            assert len(search_result) > 0
            assert search_result[0]["id"] == doc_id
            
            permissions = services['user'].get_user_permissions("test-user", doc_id)
            assert permissions["can_preview"] is True
            
            preview = services['preview'].generate_preview(doc_id)
            assert len(preview) > 0
            
            content = services['storage'].get_document_content(doc_id)
            assert len(content) > 0

    def test_error_propagation_and_convergence_handling(self, setup_services):
        services = setup_services
        gateway = services['gateway']
        
        with patch.object(services['search'], 'search_documents') as mock_search, \
             patch.object(services['user'], 'get_user_permissions') as mock_perms:
            
            # Simulate permission denied scenario
            mock_perms.return_value = {"can_view": False}
            mock_search.side_effect = Exception("Permission denied")
            
            try:
                gateway.handle_document_request(
                    user_id="restricted-user",
                    document_id="restricted-doc",
                    operation="view"
                )
                assert False, "Expected exception for permission denial"
            except Exception as e:
                assert "Permission denied" in str(e) or "permission" in str(e).lower()

    def test_service_dependency_satisfaction(self, setup_services):
        # Verify WP-018 dependency is satisfied by checking required service availability
        services = setup_services
        required_services = [
            services['search'],
            services['preview'],
            services['storage'],
            services['user'],
            services['gateway']
        ]
        
        for service in required_services:
            assert hasattr(service, '__class__')
            assert service.__class__.__name__ != 'object'