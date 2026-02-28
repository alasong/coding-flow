"""Pytest 全局配置和 Fixtures"""

import pytest
import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_response():
    """Mock LLM 响应"""
    def _mock(text: str):
        response = MagicMock()
        response.text = text
        response.__aiter__ = None
        return response
    return _mock


@pytest.fixture
def mock_dashscope_model(mock_llm_response):
    """Mock DashScope 模型"""
    with patch("agentscope.model.DashScopeChatModel") as mock:
        instance = MagicMock()
        instance.return_value = mock_llm_response('{"result": "success"}')
        instance.__call__ = AsyncMock(return_value=mock_llm_response('{"result": "success"}'))
        mock.return_value = instance
        yield mock


@pytest.fixture
def temp_output_dir(tmp_path):
    """临时输出目录"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def sample_requirements():
    """示例需求数据"""
    return {
        "functional_requirements": ["用户登录", "数据查询"],
        "non_functional_requirements": ["响应时间<1s"],
        "constraints": ["使用 PostgreSQL"]
    }


@pytest.fixture
def sample_architecture():
    """示例架构数据"""
    return {
        "system_architecture": {
            "architecture_pattern": "微服务架构",
            "system_components": [{"name": "UserService", "type": "service"}]
        },
        "technology_stack": {
            "backend": "Python FastAPI",
            "database": "PostgreSQL"
        }
    }


@pytest.fixture
def sample_decomposition_result():
    """示例项目分解结果"""
    return {
        "final_result": {
            "software_units": [
                {"id": "API::GET /users", "type": "api", "name": "GET /users"}
            ],
            "work_packages": [
                {"id": "WP-001", "name": "User Module", "software_unit_ids": ["API::GET /users"]}
            ]
        }
    }


@pytest.fixture
def disable_auth():
    """禁用认证的环境设置"""
    old_value = os.environ.get("API_KEY_ENABLED")
    os.environ["API_KEY_ENABLED"] = "false"
    yield
    if old_value is not None:
        os.environ["API_KEY_ENABLED"] = old_value
    else:
        os.environ.pop("API_KEY_ENABLED", None)


@pytest.fixture
def enable_auth():
    """启用认证的环境设置"""
    old_key = os.environ.get("API_KEY")
    old_enabled = os.environ.get("API_KEY_ENABLED")
    os.environ["API_KEY"] = "test-api-key-123"
    os.environ["API_KEY_ENABLED"] = "true"
    yield "test-api-key-123"
    if old_key is not None:
        os.environ["API_KEY"] = old_key
    else:
        os.environ.pop("API_KEY", None)
    if old_enabled is not None:
        os.environ["API_KEY_ENABLED"] = old_enabled
    else:
        os.environ.pop("API_KEY_ENABLED", None)
