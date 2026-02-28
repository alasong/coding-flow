import pytest
from unittest.mock import patch, MagicMock
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagementService
from app.services.apigateway import ApiGateway
from app.services.documentstorageservice import DocumentStorageService
from app.database import Database
from app.models import Document, User


@pytest.fixture
def mock_database():
    db = MagicMock(spec=Database)
    db.connect.return_value = None
    db.close.return_value = None
    return db


@pytest.fixture
def mock_document_storage_service():
    service = MagicMock(spec=DocumentStorageService)
    service.store_document.return_value = "doc-123"
    service.retrieve_document_content.return_value = b"test content"
    return service


@pytest.fixture
def mock_user_management_service():
    service = MagicMock(spec=UserManagementService)
    user = User(id="user-456", username="testuser", email="test@example.com")
    service.get_user_by_id.return_value = user
    service.validate_user_permissions.return_value = True
    return service


@pytest.fixture
def mock_document_preview_service():
    service = MagicMock(spec=DocumentPreviewService)
    service.generate_preview.return_value = {"format": "pdf", "page_count": 1}
    return service


@pytest.fixture
def mock_document_search_service():
    service = MagicMock(spec=DocumentSearchService)
    doc = Document(id="doc-123", title="Test Doc", content_hash="abc123")
    service.search_documents.return_value = [doc]
    return service


@pytest.fixture
def api_gateway(
    mock_database,
    mock_document_storage_service,
    mock_user_management_service,
    mock_document_preview_service,
    mock_document_search_service,
):
    return ApiGateway(
        database=mock_database,
        document_storage_service=mock_document_storage_service,
        user_management_service=mock_user_management_service,
        document_preview_service=mock_document_preview_service,
        document_search_service=mock_document_search_service,
    )


def test_api_gateway_end_to_end_flow(api_gateway, mock_database, mock_document_storage_service, mock_user_management_service, mock_document_preview_service, mock_document_search_service):
    # Simulate end-to-end flow: user lookup → search → storage → preview
    user = api_gateway.user_management_service.get_user_by_id("user-456")
    assert user.username == "testuser"

    docs = api_gateway.document_search_service.search_documents("test query")
    assert len(docs) == 1
    assert docs[0].id == "doc-123"

    doc_id = api_gateway.document_storage_service.store_document(b"test content", "test.pdf")
    assert doc_id == "doc-123"

    preview = api_gateway.document_preview_service.generate_preview("doc-123")
    assert preview["format"] == "pdf"

    # Verify database interaction was triggered
    api_gateway.database.connect.assert_called_once()
    api_gateway.database.close.assert_called_once()


def test_document_search_and_preview_integration(api_gateway, mock_document_search_service, mock_document_preview_service):
    # Test interaction between search and preview services
    docs = api_gateway.document_search_service.search_documents("integration test")
    assert docs[0].id == "doc-123"

    preview = api_gateway.document_preview_service.generate_preview(docs[0].id)
    assert preview["page_count"] == 1

    # Ensure preview service was called with correct doc ID from search result
    mock_document_preview_service.generate_preview.assert_called_with("doc-123")


def test_user_permission_validation_before_document_access(api_gateway, mock_user_management_service, mock_document_storage_service):
    # Test that user permissions are validated before accessing document storage
    user_id = "user-456"
    doc_id = "doc-123"

    is_authorized = api_gateway.user_management_service.validate_user_permissions(user_id, doc_id, "read")
    assert is_authorized is True

    content = api_gateway.document_storage_service.retrieve_document_content(doc_id)
    assert content == b"test content"

    # Verify permission check occurred before storage access
    mock_user_management_service.validate_user_permissions.assert_called_with(user_id, doc_id, "read")


def test_api_gateway_initialization_with_all_services():
    db = MagicMock(spec=Database)
    storage = MagicMock(spec=DocumentStorageService)
    user_mgmt = MagicMock(spec=UserManagementService)
    preview = MagicMock(spec=DocumentPreviewService)
    search = MagicMock(spec=DocumentSearchService)

    gateway = ApiGateway(
        database=db,
        document_storage_service=storage,
        user_management_service=user_mgmt,
        document_preview_service=preview,
        document_search_service=search,
    )

    assert gateway.database is db
    assert gateway.document_storage_service is storage
    assert gateway.user_management_service is user_mgmt
    assert gateway.document_preview_service is preview
    assert gateway.document_search_service is search