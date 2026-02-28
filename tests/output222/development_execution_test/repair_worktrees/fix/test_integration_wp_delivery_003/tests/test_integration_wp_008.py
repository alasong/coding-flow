import pytest
from app.database import get_db_session
from app.models import DocumentVersion, Document
from sqlalchemy.exc import IntegrityError
from datetime import datetime

class TestDocumentVersions:
    def test_document_version_creation_and_relationship(self, db_session):
        # Create a document first
        doc = Document(
            title="Test Document",
            content="test content",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(doc)
        db_session.flush()

        # Create document version linked to the document
        version = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            content="version 1 content",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(version)
        db_session.commit()

        # Verify relationship
        assert version.document_id == doc.id
        assert len(doc.versions) == 1
        assert doc.versions[0].id == version.id

    def test_document_version_foreign_key_constraint(self, db_session):
        # Attempt to create version with non-existent document_id
        invalid_version = DocumentVersion(
            document_id=999999,
            version_number=1,
            content="invalid version",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(invalid_version)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_document_version_ordering(self, db_session):
        # Create document
        doc = Document(
            title="Ordered Document",
            content="test",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(doc)
        db_session.flush()

        # Create multiple versions
        v1 = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            content="v1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        v2 = DocumentVersion(
            document_id=doc.id,
            version_number=2,
            content="v2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        v3 = DocumentVersion(
            document_id=doc.id,
            version_number=3,
            content="v3",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add_all([v1, v2, v3])
        db_session.commit()

        # Verify ordering by version_number (descending)
        versions = db_session.query(DocumentVersion).filter_by(document_id=doc.id).order_by(DocumentVersion.version_number.desc()).all()
        assert len(versions) == 3
        assert versions[0].version_number == 3
        assert versions[1].version_number == 2
        assert versions[2].version_number == 1

    def test_document_version_cascade_delete(self, db_session):
        # Create document with versions
        doc = Document(
            title="Cascade Test",
            content="test",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(doc)
        db_session.flush()

        v1 = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            content="cascade v1",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        v2 = DocumentVersion(
            document_id=doc.id,
            version_number=2,
            content="cascade v2",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add_all([v1, v2])
        db_session.commit()

        # Delete document
        db_session.delete(doc)
        db_session.commit()

        # Verify versions are deleted
        remaining_versions = db_session.query(DocumentVersion).filter_by(document_id=doc.id).count()
        assert remaining_versions == 0

@pytest.fixture
def db_session():
    session = get_db_session()
    try:
        yield session
        session.rollback()
    finally:
        session.close()