import pytest
import subprocess
import sys
import os
from pathlib import Path

def test_ci_pipeline_setup():
    """Test CI/CD pipeline setup by verifying required infrastructure files exist and basic build passes."""
    root_dir = Path(__file__).parent.parent
    
    # Verify essential infrastructure files exist (minimal CI setup)
    assert (root_dir / ".gitignore").exists()
    assert (root_dir / "pyproject.toml").exists() or (root_dir / "setup.py").exists()
    assert (root_dir / "requirements.txt").exists() or (root_dir / "pyproject.toml").exists()
    
    # Check that all app modules can be imported without error (basic build validation)
    app_modules = [
        "app.__init__",
        "app.database",
        "app.main",
        "app.models",
        "app.services.documentsearchservice",
        "app.services.documentpreviewservice",
        "app.services.usermanagementservice",
        "app.services.apigateway",
        "app.services.__init__",
        "app.services.documentstorageservice",
    ]
    
    for module_name in app_modules:
        try:
            __import__(module_name)
        except ImportError as e:
            raise AssertionError(f"Failed to import {module_name}: {e}")
    
    # Attempt minimal static analysis: ensure no syntax errors in core files
    for file_path in [
        root_dir / "app" / "__init__.py",
        root_dir / "app" / "database.py",
        root_dir / "app" / "main.py",
        root_dir / "app" / "models.py",
        root_dir / "app" / "services" / "documentsearchservice.py",
        root_dir / "app" / "services" / "documentpreviewservice.py",
        root_dir / "app" / "services" / "usermanagementservice.py",
        root_dir / "app" / "services" / "apigateway.py",
        root_dir / "app" / "services" / "documentstorageservice.py",
        root_dir / "app" / "services" / "__init__.py",
    ]:
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    compile(f.read(), str(file_path), "exec")
            except SyntaxError as e:
                raise AssertionError(f"Syntax error in {file_path}: {e}")
    
    # Validate service interdependencies: ensure services can be instantiated and interact minimally
    from app.services.documentsearchservice import DocumentSearchService
    from app.services.documentpreviewservice import DocumentPreviewService
    from app.services.usermanagementservice import UserManagementService
    from app.services.apigateway import ApiGateway
    from app.services.documentstorageservice import DocumentStorageService
    
    # Instantiate services to verify no import/runtime dependency failures
    _ = DocumentSearchService()
    _ = DocumentPreviewService()
    _ = UserManagementService()
    _ = ApiGateway()
    _ = DocumentStorageService()
    
    # Test basic interaction: ApiGateway should be able to reference other services
    gateway = ApiGateway()
    assert hasattr(gateway, 'search_service')
    assert hasattr(gateway, 'preview_service')
    assert hasattr(gateway, 'storage_service')
    assert hasattr(gateway, 'user_service')
    
    # Confirm all service attributes are properly initialized (not None)
    assert gateway.search_service is not None
    assert gateway.preview_service is not None
    assert gateway.storage_service is not None
    assert gateway.user_service is not None