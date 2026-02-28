import pytest
from app.services.apigateway import ApiGateway
from app.services.documentsearchservice import DocumentSearchService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.usermanagementservice import UserManagerService
from app.services.documentstorageservice import DocumentStorageService
from app.database import get_db_session
from app.models import User, Document


def test_api_convergence_end_to_end():
    # Initialize services with mocked dependencies where necessary
    db_session = get_db_session()
    
    user_service = UserManagerService(db_session)
    search_service = DocumentSearchService(db_session)
    preview_service = DocumentPreviewService(db_session)
    storage_service = DocumentStorageService(db_session)
    
    # Instantiate gateway with all dependent services
    gateway = ApiGateway(
        user_service=user_service,
        search_service=search_service,
        preview_service=preview_service,
        storage_service=storage_service
    )
    
    # Test convergence: verify all service integrations are functional
    # Create test user
    test_user = User(username="testuser", email="test@example.com")
    db_session.add(test_user)
    db_session.commit()
    
    # Create test document
    test_doc = Document(
        title="Test Convergence Doc",
        content="Convergence test content",
        user_id=test_user.id
    )
    db_session.add(test_doc)
    db_session.commit()
    
    # Verify all services respond without exception in integrated flow
    assert user_service.get_user_by_id(test_user.id) is not None
    assert search_service.search_documents("convergence") is not None
    assert preview_service.generate_preview(test_doc.id) is not None
    assert storage_service.store_document(test_doc) is True
    
    # Verify gateway orchestrates correctly
    search_result = gateway.search_documents("convergence", test_user.id)
    assert len(search_result) > 0
    
    preview = gateway.get_document_preview(test_doc.id, test_user.id)
    assert preview is not None
    
    # Cleanup
    db_session.delete(test_doc)
    db_session.delete(test_user)
    db_session.commit()


def test_api_gateway_service_dependencies():
    db_session = get_db_session()
    
    user_service = UserManagerService(db_session)
    search_service = DocumentSearchService(db_session)
    preview_service = DocumentPreviewService(db_session)
    storage_service = DocumentStorageService(db_session)
    
    gateway = ApiGateway(
        user_service=user_service,
        search_service=search_service,
        preview_service=preview_service,
        storage_service=storage_service
    )
    
    # Confirm all required service methods exist and are callable
    assert hasattr(gateway, 'search_documents')
    assert hasattr(gateway, 'get_document_preview')
    assert hasattr(gateway, 'store_document')
    assert hasattr(gateway, 'get_user_profile')
    
    # Confirm service instances are properly bound
    assert gateway.user_service == user_service
    assert gateway.search_service == search_service
    assert gateway.preview_service == preview_service
    assert gateway.storage_service == storage_service


def test_convergence_quality_metrics():
    db_session = get_db_session()
    
    user_service = UserManagerService(db_session)
    search_service = DocumentSearchService(db_session)
    preview_service = DocumentPreviewService(db_session)
    storage_service = DocumentStorageService(db_session)
    
    gateway = ApiGateway(
        user_service=user_service,
        search_service=search_service,
        preview_service=preview_service,
        storage_service=storage_service
    )
    
    # Measure response consistency across service boundaries
    test_user = User(username="quality-test", email="quality@test.com")
    db_session.add(test_user)
    db_session.commit()
    
    try:
        # Call same operation through gateway and direct service
        gateway_result = gateway.search_documents("quality", test_user.id)
        direct_result = search_service.search_documents("quality")
        
        # Assert behavioral convergence: both return non-None results
        assert gateway_result is not None
        assert direct_result is not None
        
        # Assert structural convergence: result types compatible
        assert isinstance(gateway_result, list)
        assert isinstance(direct_result, list)
        
    finally:
        db_session.delete(test_user)
        db_session.commit()