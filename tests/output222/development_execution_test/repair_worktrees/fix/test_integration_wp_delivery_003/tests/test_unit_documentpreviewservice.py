import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.documentpreviewservice import DocumentPreviewService
from unittest.mock import patch, MagicMock

@pytest.fixture
def document_preview_service():
    return DocumentPreviewService()

@pytest.fixture
def test_client():
    return TestClient(app)

def test_document_preview_service_initialization(document_preview_service):
    assert isinstance(document_preview_service, DocumentPreviewService)

@patch('app.services.documentpreviewservice.DocumentStorageService')
@patch('app.services.documentpreviewservice.DocumentSearchService')
def test_document_preview_service_dependencies(mock_search_service, mock_storage_service, document_preview_service):
    assert hasattr(document_preview_service, 'storage_service')
    assert hasattr(document_preview_service, 'search_service')
    assert mock_storage_service.called
    assert mock_search_service.called

def test_document_preview_service_get_preview_by_id(document_preview_service):
    with patch.object(document_preview_service.storage_service, 'get_document_content') as mock_get_content, \
         patch.object(document_preview_service.search_service, 'get_document_metadata') as mock_get_metadata:
        mock_get_metadata.return_value = {'id': 'doc123', 'title': 'Test Doc', 'mime_type': 'application/pdf'}
        mock_get_content.return_value = b'%PDF-1.4...'
        
        result = document_preview_service.get_preview_by_id('doc123')
        
        assert 'content' in result
        assert 'metadata' in result
        assert result['metadata']['id'] == 'doc123'
        assert len(result['content']) > 0

def test_document_preview_service_get_preview_by_id_not_found(document_preview_service):
    with patch.object(document_preview_service.search_service, 'get_document_metadata') as mock_get_metadata:
        mock_get_metadata.return_value = None
        
        result = document_preview_service.get_preview_by_id('nonexistent')
        
        assert result is None

def test_document_preview_service_generate_thumbnail(document_preview_service):
    with patch.object(document_preview_service.storage_service, 'get_document_content') as mock_get_content:
        mock_get_content.return_value = b'%PDF-1.4...'
        
        result = document_preview_service.generate_thumbnail('doc123', width=200, height=150)
        
        assert isinstance(result, bytes)
        assert len(result) > 0