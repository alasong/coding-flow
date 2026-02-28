import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import DocumentVersion
from app.services.documentstorageservice import DocumentStorageService

@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(in_memory_db):
    session = in_memory_db()
    yield session
    session.rollback()
    session.close()

def test_document_versions_table_creation(db_session):
    assert db_session.bind.dialect.name == "sqlite"

def test_document_version_model_crud(db_session):
    doc_version = DocumentVersion(
        document_id="doc123",
        version_number=1,
        storage_path="/path/to/v1.pdf",
        created_by="user456",
        status="active"
    )
    db_session.add(doc_version)
    db_session.commit()
    db_session.refresh(doc_version)
    assert doc_version.id is not None
    assert doc_version.document_id == "doc123"
    assert doc_version.version_number == 1

def test_document_storage_service_get_latest_version(db_session):
    doc_version1 = DocumentVersion(
        document_id="doc789",
        version_number=1,
        storage_path="/v1.pdf",
        created_by="user1",
        status="active"
    )
    doc_version2 = DocumentVersion(
        document_id="doc789",
        version_number=2,
        storage_path="/v2.pdf",
        created_by="user2",
        status="active"
    )
    db_session.add_all([doc_version1, doc_version2])
    db_session.commit()
    service = DocumentStorageService(db_session)
    latest = service.get_latest_version("doc789")
    assert latest is not None
    assert latest.version_number == 2

def test_document_storage_service_get_version_history(db_session):
    doc_version1 = DocumentVersion(
        document_id="doc456",
        version_number=1,
        storage_path="/v1.pdf",
        created_by="user1",
        status="active"
    )
    doc_version2 = DocumentVersion(
        document_id="doc456",
        version_number=2,
        storage_path="/v2.pdf",
        created_by="user2",
        status="archived"
    )
    db_session.add_all([doc_version1, doc_version2])
    db_session.commit()
    service = DocumentStorageService(db_session)
    history = service.get_version_history("doc456")
    assert len(history) == 2
    assert history[0].version_number == 2
    assert history[1].version_number == 1