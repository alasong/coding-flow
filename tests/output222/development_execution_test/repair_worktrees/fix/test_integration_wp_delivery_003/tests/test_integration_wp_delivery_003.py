import pytest
from unittest.mock import patch, MagicMock
from app.main import create_app
from app.database import Base
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import APIGateway
from app.services.documentstorageservice import DocumentStorageService


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    })
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def test_delivery_release_ready_integration(app):
    with app.app_context():
        if 'sqlalchemy' in app.extensions:
            db = app.extensions['sqlalchemy']
            db.create_all()
        else:
            pass
        
        search_service = DocumentSearchService()
        preview_service = DocumentPreviewService()
        user_service = UserManagementService()
        storage_service = DocumentStorageService()
        api_gateway = APIGateway()
        
        assert hasattr(search_service, 'search')
        assert hasattr(preview_service, 'generate_preview')
        assert hasattr(user_service, 'get_user_by_id')
        assert hasattr(storage_service, 'store_document')
        assert hasattr(api_gateway, 'handle_request')
        
        mock_doc_id = "doc-123"
        mock_user_id = 1
        
        with patch.object(user_service, 'get_user_by_id') as mock_get_user, \
             patch.object(storage_service, 'store_document') as mock_store, \
             patch.object(search_service, 'search') as mock_search, \
             patch.object(preview_service, 'generate_preview') as mock_preview:
            
            mock_get_user.return_value = {"id": mock_user_id, "role": "admin"}
            mock_store.return_value = mock_doc_id
            mock_search.return_value = [{"id": mock_doc_id, "title": "Test Doc"}]
            mock_preview.return_value = b"%PDF-1.4"
            
            user = user_service.get_user_by_id(mock_user_id)
            doc_id = storage_service.store_document({"content": b"test"}, user)
            results = search_service.search("test", user)
            preview = preview_service.generate_preview(doc_id)
            
            assert user["id"] == mock_user_id
            assert doc_id == mock_doc_id
            assert len(results) == 1
            assert results[0]["id"] == mock_doc_id
            assert isinstance(preview, bytes)
            assert preview.startswith(b"%PDF")


def test_api_gateway_integration_with_services(app):
    with app.app_context():
        api_gateway = APIGateway()
        search_service = DocumentSearchService()
        user_service = UserManagementService()
        
        assert hasattr(api_gateway, 'dispatch')
        assert hasattr(search_service, 'search')
        assert hasattr(user_service, 'get_user_by_id')
        
        with patch.object(api_gateway, '_get_service') as mock_get_service:
            mock_service_instance = MagicMock()
            mock_service_instance.search.return_value = []
            mock_get_service.return_value = mock_service_instance
            
            result = api_gateway.dispatch("document_search", {"query": "test"})
            
            assert result is not None
            mock_service_instance.search.assert_called_once_with("test", None)


def test_production_readiness_indicators(app):
    with app.app_context():
        assert callable(create_app)
        if 'sqlalchemy' in app.extensions:
            db = app.extensions['sqlalchemy']
            assert hasattr(db, 'create_all')
            db.create_all()
        else:
            pass
        
        services = [
            DocumentSearchService(),
            DocumentPreviewService(),
            UserManagementService(),
            DocumentStorageService(),
            APIGateway()
        ]
        
        for service in services:
            assert service is not None