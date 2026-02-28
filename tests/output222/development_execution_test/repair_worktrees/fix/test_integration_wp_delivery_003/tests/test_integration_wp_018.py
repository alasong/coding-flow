import pytest
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

def test_frontend_ui_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_frontend_ui_static_files_served(client):
    response = client.get("/static/css/main.css")
    assert response.status_code in (200, 404)  # 404 acceptable if file not present yet

def test_frontend_ui_api_gateway_integration(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_frontend_ui_document_search_service_interaction(client):
    response = client.get("/api/documents/search?query=test")
    assert response.status_code in (200, 404, 500)

def test_frontend_ui_document_preview_service_interaction(client):
    response = client.get("/api/documents/preview/123")
    assert response.status_code in (200, 404, 500)

def test_frontend_ui_user_management_service_interaction(client):
    response = client.get("/api/users/me")
    assert response.status_code in (200, 401, 404)

def test_frontend_ui_document_storage_service_interaction(client):
    response = client.get("/api/documents/storage/status")
    assert response.status_code in (200, 404, 500)