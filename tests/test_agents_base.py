"""BaseAgent 单元测试"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# 配置 pytest-asyncio
pytestmark = pytest.mark.anyio


class TestBaseAgent:
    """BaseAgent 测试类"""

    def test_agent_initialization(self, disable_auth, mock_dashscope_model):
        """测试 Agent 初始化"""
        from agents.base_agent import BaseAgent
        
        with patch("agents.base_agent.DASHSCOPE_API_KEY", "test-key"):
            agent = BaseAgent(
                name="test_agent",
                model_config_name="test",
                model_name="qwen-turbo"
            )
            assert agent.name == "test_agent"
            assert agent.target_model_name == "qwen-turbo"

    def test_agent_task_type_precision(self, disable_auth):
        """测试 Agent 精确性任务类型"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(
            name="test",
            model_config_name="test",
            task_type="precision"
        )
        assert agent.task_type == "precision"

    def test_agent_task_type_creativity(self, disable_auth):
        """测试 Agent 创造性任务类型"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(
            name="test",
            model_config_name="test",
            task_type="creativity"
        )
        assert agent.task_type == "creativity"

    async def test_process_model_response_text(self, disable_auth):
        """测试文本响应处理"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(name="test", model_config_name="test")

        # 创建一个简单的 mock 响应对象
        class MockResponse:
            text = "Hello World"
        
        mock_response = MockResponse()

        result = await agent._process_model_response(mock_response)
        assert result == "Hello World"

    async def test_process_model_response_streaming(self, disable_auth):
        """测试流式响应处理"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(name="test", model_config_name="test")

        # 创建一个支持异步迭代的 mock 响应
        class MockChunk:
            def __init__(self, text):
                self.text = text
        
        class MockStreamingResponse:
            def __init__(self, chunks):
                self.chunks = chunks
            
            def __aiter__(self):
                return self._async_generator()
            
            async def _async_generator(self):
                for chunk in self.chunks:
                    yield chunk
        
        mock_response = MockStreamingResponse([
            MockChunk("Hello"),
            MockChunk(" World")
        ])

        result = await agent._process_model_response(mock_response)
        # 流式响应应该包含内容
        assert len(result) > 0

    def test_extract_json_valid(self, disable_auth):
        """测试 JSON 提取"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(name="test", model_config_name="test")

        content = '```json\n{"key": "value"}\n```'
        result = agent._extract_json(content)
        assert result == {"key": "value"}

    def test_extract_json_without_code_block(self, disable_auth):
        """测试无代码块的 JSON 提取"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(name="test", model_config_name="test")

        content = 'Some text before {"key": "value"} some text after'
        result = agent._extract_json(content)
        assert result == {"key": "value"}

    def test_extract_json_list(self, disable_auth):
        """测试 JSON 列表提取"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(name="test", model_config_name="test")

        content = '[{"id": 1}, {"id": 2}]'
        result = agent._extract_json(content, expected_type=list)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_extract_json_invalid(self, disable_auth):
        """测试无效 JSON 处理"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(name="test", model_config_name="test")

        result = agent._extract_json("not json at all")
        assert result is None

    def test_extract_json_empty(self, disable_auth):
        """测试空内容 JSON 提取"""
        from agents.base_agent import BaseAgent
        
        agent = BaseAgent(name="test", model_config_name="test")

        result = agent._extract_json("")
        assert result is None


class TestLLMConfig:
    """LLMConfig 配置测试"""

    def test_default_generate_kwargs(self):
        """测试默认生成参数"""
        from config import LLMConfig
        
        kwargs = LLMConfig.get_generate_kwargs("default")
        assert "temperature" in kwargs
        assert "max_tokens" in kwargs
        assert kwargs["temperature"] == LLMConfig.TEMPERATURE_CREATIVITY

    def test_precision_generate_kwargs(self):
        """测试精确性任务生成参数"""
        from config import LLMConfig
        
        kwargs = LLMConfig.get_generate_kwargs("precision")
        assert kwargs["temperature"] == LLMConfig.TEMPERATURE_PRECISION

    def test_long_generate_kwargs(self):
        """测试长文档任务生成参数"""
        from config import LLMConfig
        
        kwargs = LLMConfig.get_generate_kwargs("long")
        assert kwargs["max_tokens"] == LLMConfig.MAX_TOKENS_LONG

    def test_retry_config(self):
        """测试重试配置"""
        from config import LLMConfig
        
        config = LLMConfig.get_retry_config()
        assert "max_retries" in config
        assert "initial_delay" in config
        assert config["max_retries"] == LLMConfig.MAX_RETRIES


class TestRequirementCollectorAgent:
    """RequirementCollectorAgent 测试"""

    def test_agent_initialization(self, disable_auth):
        """测试需求收集 Agent 初始化"""
        from agents.requirement_collector import RequirementCollectorAgent
        
        agent = RequirementCollectorAgent()
        assert agent.name == "需求收集专家"
        assert agent.task_type == "creativity"

    def test_offline_parse_requirements(self, disable_auth):
        """测试离线需求解析"""
        from agents.requirement_collector import RequirementCollectorAgent
        
        agent = RequirementCollectorAgent()
        result = agent._offline_parse_requirements("开发一个用户管理系统，需要高性能和安全认证")
        
        assert "raw_input" in result
        assert "functional_requirements" in result
        assert "non_functional_requirements" in result

    def test_extract_valid_items(self, disable_auth):
        """测试有效项提取"""
        from agents.requirement_collector import RequirementCollectorAgent
        
        agent = RequirementCollectorAgent()
        content = """
        ## 功能需求
        - 用户登录
        - 数据查询
        ## 非功能需求
        - 响应时间小于1秒
        """
        
        items = agent._extract_valid_items(content)
        assert len(items) > 0
        # 应该包含提取的项目
        assert any("登录" in item or "查询" in item for item in items)

    def test_classify_items(self, disable_auth):
        """测试需求项分类"""
        from agents.requirement_collector import RequirementCollectorAgent
        
        agent = RequirementCollectorAgent()
        # 使用明确的测试数据
        items = ["商品管理", "系统响应性能", "数据库选型"]
        
        functional, non_functional, constraints, key_features = agent._classify_items(items)
        
        # 检查分类结果：至少应该有一些分类
        total_classified = len(functional) + len(non_functional) + len(constraints) + len(key_features)
        assert total_classified == len(items)
