"""安全模块测试"""

import pytest
import os
import time

# 配置 pytest-asyncio
pytestmark = pytest.mark.anyio


class TestCommandExecutor:
    """命令执行安全测试"""

    def test_validate_allowed_command(self):
        """测试允许的命令"""
        from utils.command_executor import validate_command
        
        cmd, args = validate_command("docker compose up -d")
        assert cmd == "docker"
        assert "compose" in args
        assert "up" in args

    def test_validate_blocked_command(self):
        """测试禁止的命令"""
        from utils.command_executor import validate_command, CommandExecutionError
        
        with pytest.raises(CommandExecutionError):
            validate_command("rm -rf /")

    def test_validate_shell_injection(self):
        """测试 Shell 注入防护"""
        from utils.command_executor import validate_command, CommandExecutionError
        
        with pytest.raises(CommandExecutionError):
            validate_command("docker compose up -d; rm -rf /")

    def test_validate_empty_command(self):
        """测试空命令"""
        from utils.command_executor import validate_command, CommandExecutionError
        
        with pytest.raises(CommandExecutionError):
            validate_command("")

    def test_validate_unknown_command(self):
        """测试未知命令"""
        from utils.command_executor import validate_command, CommandExecutionError
        
        with pytest.raises(CommandExecutionError):
            validate_command("bash -c 'echo hello'")


class TestAuth:
    """认证模块测试"""

    @pytest.mark.asyncio
    async def test_api_key_verification_disabled(self, disable_auth):
        """测试 API Key 验证（禁用状态）"""
        from infra.auth import verify_api_key
        
        result = await verify_api_key(None)
        assert result is True

    @pytest.mark.asyncio
    async def test_api_key_verification_enabled_valid(self, enable_auth):
        """测试 API Key 验证（启用状态 - 有效 Key）"""
        from infra.auth import verify_api_key
        from unittest.mock import MagicMock
        
        # 模拟请求头中的 API Key
        api_key = enable_auth
        result = await verify_api_key(api_key)
        assert result is True

    @pytest.mark.asyncio
    async def test_api_key_verification_enabled_invalid(self, enable_auth):
        """测试 API Key 验证（启用状态 - 无效 Key）"""
        from infra.auth import verify_api_key
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("invalid-key")
        assert exc_info.value.status_code == 401

    def test_ws_token_verification_disabled(self, disable_auth):
        """测试 WebSocket Token 验证（禁用状态）"""
        from infra.auth import verify_ws_token
        
        result = verify_ws_token(None)
        assert result is True

    def test_ws_token_verification_enabled_valid(self, enable_auth):
        """测试 WebSocket Token 验证（启用状态 - 有效 Token）"""
        from infra.auth import verify_ws_token
        
        api_key = enable_auth
        # 生成有效 token
        valid_token = f"{api_key}{int(time.time())}"
        result = verify_ws_token(valid_token)
        assert result is True

    def test_ws_token_verification_enabled_invalid(self, enable_auth):
        """测试 WebSocket Token 验证（启用状态 - 无效 Token）"""
        from infra.auth import verify_ws_token
        
        result = verify_ws_token("invalid-token")
        assert result is False

    def test_ws_token_expired(self, enable_auth):
        """测试 WebSocket Token 过期"""
        from infra.auth import verify_ws_token
        
        api_key = enable_auth
        # 生成过期 token（10分钟前）
        expired_time = int(time.time()) - 600
        expired_token = f"{api_key}{expired_time}"
        result = verify_ws_token(expired_token)
        assert result is False


class TestExceptions:
    """自定义异常测试"""

    def test_coding_flow_error(self):
        """测试基础异常类"""
        from utils.exceptions import CodingFlowError
        
        error = CodingFlowError("测试错误", context={"key": "value"})
        assert error.message == "测试错误"
        assert error.context == {"key": "value"}
        assert "测试错误" in str(error)

    def test_llm_error(self):
        """测试 LLM 错误"""
        from utils.exceptions import LLMError
        
        error = LLMError("LLM 调用失败")
        assert isinstance(error, Exception)
        assert error.message == "LLM 调用失败"

    def test_agent_error(self):
        """测试 Agent 错误"""
        from utils.exceptions import AgentError
        
        error = AgentError("Agent 执行失败", context={"agent": "test"})
        assert error.context["agent"] == "test"

    def test_workflow_error(self):
        """测试工作流错误"""
        from utils.exceptions import WorkflowError
        
        error = WorkflowError("工作流执行失败")
        assert error.message == "工作流执行失败"

    def test_validation_error(self):
        """测试验证错误"""
        from utils.exceptions import ValidationError
        
        error = ValidationError("验证失败")
        assert isinstance(error, Exception)
