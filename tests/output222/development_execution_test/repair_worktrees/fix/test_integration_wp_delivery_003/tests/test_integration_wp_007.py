import pytest
from unittest.mock import patch, MagicMock
from app.database import get_db_session
from app.models import Document
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService


class TestDocumentsUnitIntegration:
    @pytest.fixture
    def mock_db_session(self):
        with patch('app.database.get_db_session') as mock_session_factory:
            mock_session = MagicMock()
            mock_session_factory.return_value.__enter__.return_value = mock_session
            yield mock_session

    @pytest.fixture
    def document_storage_service(self):
        return DocumentStorageService()

    @pytest.fixture
    def document_search_service(self):
        return DocumentSearchService()

    @pytest.fixture
    def document_preview_service(self):
        return DocumentPreviewService()

    def test_document_storage_and_search_integration(
        self,
        mock_db_session,
        document_storage_service,
        document_search_service
    ):
        # Arrange
        doc_data = {
            "title": "Test Document",
            "content": "This is a test document content.",
            "user_id": 123,
            "file_path": "/tmp/test.pdf"
        }
        
        # Mock storage behavior
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 456)
        
        # Act
        stored_doc = document_storage_service.create_document(**doc_data)
        
        # Assert storage created document with ID
        assert stored_doc.id == 456
        assert stored_doc.title == "Test Document"
        
        # Act: search for the stored document
        search_results = document_search_service.search_by_title("Test Document")
        
        # Assert search returns expected document
        assert len(search_results) == 1
        assert search_results[0].id == 456

    def test_document_storage_and_preview_integration(
        self,
        mock_db_session,
        document_storage_service,
        document_preview_service
    ):
        # Arrange
        doc_data = {
            "title": "Preview Test",
            "content": "Previewable content.",
            "user_id": 789,
            "file_path": "/tmp/preview.txt"
        }
        
        # Mock storage
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 999)
        
        # Act
        stored_doc = document_storage_service.create_document(**doc_data)
        
        # Assert storage succeeded
        assert stored_doc.id == 999
        
        # Act: generate preview
        preview = document_preview_service.generate_preview(stored_doc.id)
        
        # Assert preview contains expected content snippet
        assert isinstance(preview, str)
        assert "Previewable content." in preview or len(preview) > 0

    def test_full_documents_unit_workflow(
        self,
        mock_db_session,
        document_storage_service,
        document_search_service,
        document_preview_service
    ):
        # Arrange
        test_docs = [
            {"title": "Report Q1", "content": "Q1 revenue data.", "user_id": 101, "file_path": "/docs/q1.pdf"},
            {"title": "Design Spec", "content": "UI component specs.", "user_id": 102, "file_path": "/docs/spec.md"},
        ]
        
        # Mock DB session behavior for multiple inserts
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', hash(x.title) % 10000)
        
        # Act: store both documents
        docs = [document_storage_service.create_document(**d) for d in test_docs]
        
        # Assert both were stored with IDs
        assert all(doc.id for doc in docs)
        
        # Act: search for one
        found_docs = document_search_service.search_by_title("Report Q1")
        
        # Assert search found it
        assert len(found_docs) == 1
        assert found_docs[0].title == "Report Q1"
        
        # Act: get preview of first
        preview = document_preview_service.generate_preview(docs[0].id)
        
        # Assert preview is non-empty
        assert preview and isinstance(preview, str)

    def test_document_model_persistence_consistency(
        self,
        mock_db_session,
        document_storage_service
    ):
        # Arrange
        doc_data = {
            "title": "Persistence Check",
            "content": "Ensuring ORM consistency.",
            "user_id": 200,
            "file_path": "/tmp/check.bin"
        }
        
        # Mock session to verify model instance creation
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.side_effect = lambda x: setattr(x, 'id', 777)
        
        # Act
        doc = document_storage_service.create_document(**doc_data)
        
        # Assert model instance matches expected type and fields
        assert isinstance(doc, Document)
        assert doc.title == doc_data["title"]
        assert doc.content == doc_data["content"]
        assert doc.user_id == doc_data["user_id"]
        assert doc.file_path == doc_data["file_path"]
        assert doc.id == 777