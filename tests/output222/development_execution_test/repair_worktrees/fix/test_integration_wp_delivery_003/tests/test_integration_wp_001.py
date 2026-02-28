import pytest
from app.services.documentstorageservice import DocumentStorageService
from unittest.mock import patch, MagicMock
import tempfile
import os

@pytest.fixture
def document_storage_service():
    return DocumentStorageService()

def test_store_document_success(document_storage_service):
    content = "test content"
    doc_id = document_storage_service.store_document(content)
    assert doc_id is not None
    assert doc_id.startswith("doc_")

def test_retrieve_document_success(document_storage_service):
    content = "test content"
    doc_id = document_storage_service.store_document(content)
    
    doc = document_storage_service.retrieve_document(doc_id)
    assert doc is not None
    assert doc["id"] == doc_id
    assert doc["content"] == content

def test_retrieve_document_not_found(document_storage_service):
    with pytest.raises(KeyError):
        document_storage_service.retrieve_document("nonexistent_id")

def test_update_document_success(document_storage_service):
    content = "test content"
    doc_id = document_storage_service.store_document(content)
    
    new_content = "updated content"
    result = document_storage_service.update_document(doc_id, content=new_content)
    assert result is True
    
    doc = document_storage_service.retrieve_document(doc_id)
    assert doc["content"] == new_content

def test_update_document_not_found(document_storage_service):
    result = document_storage_service.update_document("nonexistent_id", content="new")
    assert result is False

def test_delete_document_success(document_storage_service):
    content = "test content"
    doc_id = document_storage_service.store_document(content)
    
    result = document_storage_service.delete_document(doc_id)
    assert result is True
    
    with pytest.raises(KeyError):
        document_storage_service.retrieve_document(doc_id)

def test_delete_document_not_found(document_storage_service):
    result = document_storage_service.delete_document("nonexistent_id")
    assert result is False

def test_list_document_ids(document_storage_service):
    document_storage_service.store_document("doc1")
    document_storage_service.store_document("doc2")
    
    ids = document_storage_service.list_document_ids()
    assert len(ids) == 2
    assert isinstance(ids, list)

def test_get_document_count(document_storage_service):
    assert document_storage_service.get_document_count() == 0
    document_storage_service.store_document("doc1")
    assert document_storage_service.get_document_count() == 1
