from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

# Mock service classes based on mapping
class UserManagementService:
    def create_user(self, user_data: dict) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "name": user_data.get("name", "Unknown"),
            "email": user_data.get("email", ""),
            "created_at": datetime.utcnow().isoformat()
        }

    def get_user(self, user_id: str) -> dict:
        if user_id == "notfound":
            raise ValueError("User not found")
        return {
            "id": user_id,
            "name": "John Doe",
            "email": "john@example.com",
            "created_at": datetime.utcnow().isoformat()
        }

class DocumentStorageService:
    def create_document(self, doc_data: dict) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "title": doc_data.get("title", "Untitled"),
            "content_type": doc_data.get("content_type", "text/plain"),
            "size": doc_data.get("size", 0),
            "created_at": datetime.utcnow().isoformat()
        }

    def get_document(self, document_id: str) -> dict:
        if document_id == "notfound":
            raise ValueError("Document not found")
        return {
            "id": document_id,
            "title": "Sample Document",
            "content_type": "application/pdf",
            "size": 102400,
            "created_at": datetime.utcnow().isoformat()
        }

class DocumentPreviewService:
    def get_preview(self, document_id: str) -> dict:
        if document_id == "notfound":
            raise ValueError("Document not found")
        return {
            "document_id": document_id,
            "preview_url": f"https://preview.example.com/{document_id}",
            "format": "png",
            "width": 800,
            "height": 600
        }

class DocumentSearchService:
    def search_in_document(self, document_id: str, query: str) -> dict:
        if document_id == "notfound":
            raise ValueError("Document not found")
        return {
            "document_id": document_id,
            "query": query,
            "results": [
                {"page": 1, "snippet": "This is a sample match snippet.", "score": 0.95}
            ],
            "total_matches": 1
        }

class APIGateway:
    pass

# Import services as per mapping
from app.services.usermanagementservice import UserManagementService
from app.services.documentstorageservice import DocumentStorageService
from app.services.documentpreviewservice import DocumentPreviewService
from app.services.documentsearchservice import DocumentSearchService
from app.services.apigateway import APIGateway

# Pydantic models
class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    content_type: str = Field(default="text/plain")
    size: int = Field(ge=0, default=0)

class DocumentVersion(BaseModel):
    id: str
    number: int
    created_at: str
    size: int

class DocumentVersionsResponse(BaseModel):
    document_id: str
    versions: List[DocumentVersion]

# Initialize services
user_service = UserManagementService()
document_service = DocumentStorageService()
preview_service = DocumentPreviewService()
search_service = DocumentSearchService()
api_gateway = APIGateway()

app = FastAPI(
    title="API Gateway Service",
    version="1.0.0",
    description="RESTful API for users and documents"
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/users", response_model=dict)
def create_user(user: UserCreateRequest):
    try:
        result = user_service.create_user(user.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@app.get("/api/v1/users/{userId}", response_model=dict)
def get_user(userId: str):
    try:
        result = user_service.get_user(userId)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user: {str(e)}")

@app.post("/api/v1/documents", response_model=dict)
def create_document(document: DocumentCreateRequest):
    try:
        result = document_service.create_document(document.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

@app.get("/api/v1/documents/{documentId}", response_model=dict)
def get_document(documentId: str):
    try:
        result = document_service.get_document(documentId)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

@app.get("/api/v1/documents/{documentId}/preview", response_model=dict)
def get_document_preview(documentId: str):
    try:
        result = preview_service.get_preview(documentId)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve preview: {str(e)}")

@app.get("/api/v1/documents/{documentId}/versions", response_model=DocumentVersionsResponse)
def list_document_versions(documentId: str):
    # Simulate returning versions
    try:
        versions = [
            DocumentVersion(
                id=str(uuid.uuid4()),
                number=1,
                created_at=datetime.utcnow().isoformat(),
                size=102400
            ),
            DocumentVersion(
                id=str(uuid.uuid4()),
                number=2,
                created_at=datetime.utcnow().isoformat(),
                size=105200
            )
        ]
        return DocumentVersionsResponse(document_id=documentId, versions=versions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")

@app.get("/api/v1/documents/{documentId}/search", response_model=dict)
def search_in_document(documentId: str, q: str = Query(..., alias="q", min_length=1)):
    try:
        result = search_service.search_in_document(documentId, q)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/v1/documents/{documentId}/versions/{versionId}", response_model=dict)
def get_document_version(documentId: str, versionId: str):
    # Simulate version retrieval
    try:
        return {
            "document_id": documentId,
            "version_id": versionId,
            "number": 1,
            "content_hash": "sha256:abc123...",
            "download_url": f"https://storage.example.com/{documentId}/v/{versionId}",
            "size": 102400,
            "created_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve version: {str(e)}")

def create_app() -> FastAPI:
    return app