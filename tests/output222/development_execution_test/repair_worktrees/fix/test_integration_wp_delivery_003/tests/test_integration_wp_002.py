import pytest
from unittest.mock import Mock, patch
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentsearchservice import DocumentSearchService
from app.services.usermanagementservice import UserManagerService


class TestDocumentPreviewService:
    @pytest.fixture
    def mock_dependencies(self):
        return {
            "document_storage_service": Mock(spec=DocumentStorageService),
            "document_search_service": Mock(spec=DocumentSearchService),
            "user_manager_service": Mock(spec=UserManagerService),
        }

    @pytest.fixture
    def preview_service(self, mock_dependencies):
        return DocumentPreviewService(
            document_storage_service=mock_dependencies["document_storage_service"],
            document_search_service=mock_dependencies["document_search_service"],
            user_manager_service=mock_dependencies["user_manager_service"],
        )

    def test_get_preview_success(self, preview_service, mock_dependencies):
        # Arrange
        doc_id = "doc-123"
        user_id = "user-456"
        mock_dependencies["document_search_service"].get_document_metadata.return_value = {
            "id": doc_id,
            "file_path": "/storage/docs/report.pdf",
            "mime_type": "application/pdf",
        }
        mock_dependencies["document_storage_service"].get_preview_content.return_value = b"%PDF-1.4..."
        mock_dependencies["user_manager_service"].can_access_document.return_value = True

        # Act
        result = preview_service.get_preview(doc_id, user_id)

        # Assert
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0
        mock_dependencies["document_search_service"].get_document_metadata.assert_called_once_with(doc_id)
        mock_dependencies["user_manager_service"].can_access_document.assert_called_once_with(user_id, doc_id)
        mock_dependencies["document_storage_service"].get_preview_content.assert_called_once_with(
            "/storage/docs/report.pdf", "application/pdf"
        )

    def test_get_preview_unauthorized_access(self, preview_service, mock_dependencies):
        # Arrange
        doc_id = "doc-123"
        user_id = "user-456"
        mock_dependencies["user_manager_service"].can_access_document.return_value = False

        # Act & Assert
        with pytest.raises(PermissionError, match="User does not have access to document"):
            preview_service.get_preview(doc_id, user_id)

        mock_dependencies["user_manager_service"].can_access_document.assert_called_once_with(user_id, doc_id)

    def test_get_preview_document_not_found(self, preview_service, mock_dependencies):
        # Arrange
        doc_id = "doc-123"
        user_id = "user-456"
        mock_dependencies["document_search_service"].get_document_metadata.return_value = None
        mock_dependencies["user_manager_service"].can_access_document.return_value = True

        # Act & Assert
        with pytest.raises(ValueError, match="Document not found"):
            preview_service.get_preview(doc_id, user_id)

        mock_dependencies["document_search_service"].get_document_metadata.assert_called_once_with(doc_id)

    def test_get_preview_storage_failure(self, preview_service, mock_dependencies):
        # Arrange
        doc_id = "doc-123"
        user_id = "user-456"
        mock_dependencies["document_search_service"].get_document_metadata.return_value = {
            "id": doc_id,
            "file_path": "/storage/docs/report.pdf",
            "mime_type": "application/pdf",
        }
        mock_dependencies["user_manager_service"].can_access_document.return_value = True
        mock_dependencies["document_storage_service"].get_preview_content.side_effect = RuntimeError("Storage unavailable")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Storage unavailable"):
            preview_service.get_preview(doc_id, user_id)

    def test_get_preview_mime_type_handling(self, preview_service, mock_dependencies):
        # Arrange
        doc_id = "doc-123"
        user_id = "user-456"
        mock_dependencies["document_search_service"].get_document_metadata.return_value = {
            "id": doc_id,
            "file_path": "/storage/docs/image.png",
            "mime_type": "image/png",
        }
        mock_dependencies["document_storage_service"].get_preview_content.return_value = b"\x89PNG\r\n\x1a\n"
        mock_dependencies["user_manager_service"].can_access_document.return_value = True

        # Act
        result = preview_service.get_preview(doc_id, user_id)

        # Assert
        assert result is not None
        assert isinstance(result, bytes)
        mock_dependencies["document_storage_service"].get_preview_content.assert_called_once_with(
            "/storage/docs/image.png", "image/png"
        )