import pytest
from app.database import get_db_session
from app.models import Document
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentpreviewservice import DocumentPreviewService
from sqlalchemy.exc import IntegrityError
from datetime import datetime

@pytest.fixture
def db_session():
    session = get_db_session()
    try:
        yield session
        session.rollback()
    finally:
        session.close()

@pytest.fixture
def document_storage_service(db_session):
    return DocumentStorageService(db_session)

@pytest.fixture
def document_preview_service(db_session):
    return DocumentPreviewService(db_session)

@pytest.fixture
def document_search_service(db_session):
    return DocumentSearchService(db_session)

def test_document_search_index_creation_and_query(db_session, document_storage_service, document_search_service):
    # Create test document via storage service
    doc_id = document_storage_service.store_document(
        title="Test Search Index Document",
        content="This is a test document for full-text search indexing.",
        mime_type="text/plain",
        file_size=42,
        user_id=1
    )
    
    # Ensure document exists and has searchable content
    doc = db_session.query(Document).filter_by(id=doc_id).first()
    assert doc is not None
    assert doc.title == "Test Search Index Document"
    
    # Trigger index update (assuming service handles indexing on store)
    # Verify index contains expected terms via search service
    results = document_search_service.search("test document")
    assert len(results) >= 1
    assert any(r.id == doc_id for r in results)
    
    # Verify exact phrase match
    phrase_results = document_search_service.search('"full-text search"')
    assert len(phrase_results) == 0  # Not present in content
    
    # Verify partial word match
    partial_results = document_search_service.search("docu*")
    assert len(partial_results) >= 1
    assert any(r.id == doc_id for r in partial_results)

def test_document_search_index_consistency_after_update(db_session, document_storage_service, document_search_service):
    # Store initial document
    doc_id = document_storage_service.store_document(
        title="Initial Title",
        content="Initial content for indexing.",
        mime_type="text/plain",
        file_size=35,
        user_id=1
    )
    
    # Update document content
    document_storage_service.update_document_content(
        doc_id=doc_id,
        new_content="Updated content for indexing with new terms.",
        new_title="Updated Title"
    )
    
    # Search for new terms
    updated_results = document_search_service.search("Updated content")
    assert len(updated_results) >= 1
    assert updated_results[0].id == doc_id
    
    # Search for old terms should still work if index is maintained
    old_term_results = document_search_service.search("Initial")
    assert len(old_term_results) == 0  # Index reflects current state only

def test_document_search_index_empty_content_handling(db_session, document_storage_service, document_search_service):
    # Store document with empty content
    doc_id = document_storage_service.store_document(
        title="Empty Content Doc",
        content="",
        mime_type="text/plain",
        file_size=0,
        user_id=1
    )
    
    # Search should not crash and return no results for non-title terms
    results = document_search_service.search("nonexistent")
    assert len(results) == 0
    
    # Search by title should find it
    title_results = document_search_service.search("Empty Content Doc")
    assert len(title_results) == 1
    assert title_results[0].id == doc_id

def test_document_search_index_case_insensitivity(db_session, document_storage_service, document_search_service):
    doc_id = document_storage_service.store_document(
        title="CASE SENSITIVE TEST",
        content="mixed case content here.",
        mime_type="text/plain",
        file_size=32,
        user_id=1
    )
    
    # All variations should match
    upper_results = document_search_service.search("CASE")
    lower_results = document_search_service.search("case")
    mixed_results = document_search_service.search("Case")
    
    assert len(upper_results) == 1
    assert len(lower_results) == 1
    assert len(mixed_results) == 1
    assert upper_results[0].id == doc_id
    assert lower_results[0].id == doc_id
    assert mixed_results[0].id == doc_id

def test_document_search_index_special_characters(db_session, document_storage_service, document_search_service):
    doc_id = document_storage_service.store_document(
        title="Special Chars: @#$%",
        content="Content with symbols: !@# and punctuation.",
        mime_type="text/plain",
        file_size=48,
        user_id=1
    )
    
    # Search should handle special chars appropriately (typically ignored or treated as separators)
    results = document_search_service.search("symbols")
    assert len(results) == 1
    assert results[0].id == doc_id
    
    # Punctuation in search term should not break query
    punct_results = document_search_service.search("punctuation.")
    assert len(punct_results) == 1
    assert punct_results[0].id == doc_id