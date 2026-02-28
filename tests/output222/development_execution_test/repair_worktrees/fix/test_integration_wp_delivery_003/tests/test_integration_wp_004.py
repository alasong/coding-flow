import pytest
from unittest.mock import Mock, patch
from app.services.apigateway import APIGateway
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagementService
from app.services.documentstorageservice import DocumentStorageService


class TestAPIGatewayIntegration:
    @pytest.fixture
    def api_gateway(self):
        return APIGateway()

    @pytest.fixture
    def mock_services(self):
        with patch('app.services.apigateway.DocumentSearchService') as mock_search, \
             patch('app.services.apigateway.DocumentPreviewService') as mock_preview, \
             patch('app.services.apigateway.UserManagementService') as mock_user, \
             patch('app.services.apigateway.DocumentStorageService') as mock_storage:
            mock_search.return_value = Mock(spec=DocumentSearchService)
            mock_preview.return_value = Mock(spec=DocumentPreviewService)
            mock_user.return_value = Mock(spec=UserManagementService)
            mock_storage.return_value = Mock(spec=DocumentStorageService)
            yield {
                'search': mock_search.return_value,
                'preview': mock_preview.return_value,
                'user': mock_user.return_value,
                'storage': mock_storage.return_value
            }

    def test_api_gateway_initializes_all_required_services(self, api_gateway, mock_services):
        assert hasattr(api_gateway, 'search_service')
        assert hasattr(api_gateway, 'preview_service')
        assert hasattr(api_gateway, 'user_service')
        assert hasattr(api_gateway, 'storage_service')

    def test_api_gateway_forward_search_request(self, api_gateway, mock_services):
        query = "test query"
        api_gateway.search(query)
        mock_services['search'].search.assert_called_once_with(query)

    def test_api_gateway_forward_preview_request(self, api_gateway, mock_services):
        doc_id = "doc-123"
        api_gateway.get_preview(doc_id)
        mock_services['preview'].get_preview.assert_called_once_with(doc_id)

    def test_api_gateway_forward_user_operation(self, api_gateway, mock_services):
        user_data = {"username": "testuser"}
        api_gateway.create_user(user_data)
        mock_services['user'].create_user.assert_called_once_with(user_data)

    def test_api_gateway_forward_storage_operation(self, api_gateway, mock_services):
        doc_content = b"test content"
        api_gateway.store_document(doc_content)
        mock_services['storage'].store_document.assert_called_once_with(doc_content)

    def test_api_gateway_health_check_returns_all_services_healthy(self, api_gateway, mock_services):
        result = api_gateway.health_check()
        assert result['status'] == 'healthy'
        assert len(result['services']) == 4
        assert all(service['status'] == 'healthy' for service in result['services'])

    def test_api_gateway_handles_service_unavailable_during_health_check(self, api_gateway):
        with patch('app.services.apigateway.DocumentSearchService') as mock_search, \
             patch('app.services.apigateway.DocumentPreviewService') as mock_preview, \
             patch('app.services.apigateway.UserManagementService') as mock_user, \
             patch('app.services.apigateway.DocumentStorageService') as mock_storage:
            mock_search.side_effect = Exception("Service unavailable")
            mock_preview.return_value = Mock(spec=DocumentPreviewService)
            mock_user.return_value = Mock(spec=UserManagementService)
            mock_storage.return_value = Mock(spec=DocumentStorageService)
            
            result = api_gateway.health_check()
            assert result['status'] == 'degraded'
            failed_services = [s for s in result['services'] if s['status'] == 'unavailable']
            assert len(failed_services) == 1
            assert failed_services[0]['name'] == 'DocumentSearchService'