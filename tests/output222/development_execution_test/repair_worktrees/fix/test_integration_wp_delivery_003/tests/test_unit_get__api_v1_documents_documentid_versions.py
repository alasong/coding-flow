import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Document, DocumentVersion

@pytest.fixture(scope="function")
def test_client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(test_engine)

def test_get_document_versions_success(test_client, db_session):
    doc = Document(id=1, title="Test Doc", content="content", created_by=1)
    db_session.add(doc)
    db_session.commit()
    version1 = DocumentVersion(document_id=1, version_number=1, content="v1 content", created_by=1)
    version2 = DocumentVersion(document_id=1, version_number=2, content="v2 content", created_by=1)
    db_session.add(version1)
    db_session.add(version2)
    db_session.commit()
    response = test_client.get("/api/v1/documents/1/versions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["version_number"] == 1
    assert data[1]["version_number"] == 2

def test_get_document_versions_not_found(test_client, db_session):
    response = test_client.get("/api/v1/documents/999/versions")
    assert response.status_code == 404

def test_get_document_versions_empty(test_client, db_session):
    doc = Document(id=2, title="Empty Doc", content="content", created_by=1)
    db_session.add(doc)
    db_session.commit()
    response = test_client.get("/api/v1/documents/2/versions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0