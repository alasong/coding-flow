import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from agentscope.agent import AgentBase
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

# 全局信号量，控制所有Agent的总并发请求数，避免触发API限流
# 将并发限制为 3，以安全地应对 DashScope 的限流策略
GLOBAL_LLM_SEMAPHORE = asyncio.Semaphore(3)

class BaseAgent(AgentBase):
    """Agent基类 - 所有Agent的抽象基类"""
    
    def __init__(self, name: str, model_config_name: str, model_name: str = None, **kwargs):
        """
        初始化Agent基类
        
        Args:
            name: Agent名称
            model_config_name: 模型配置名称
            model_name: 指定使用的模型名称，如果为None则使用默认模型
        """
        super().__init__()
        self.name = name
        self.model_config_name = model_config_name
        self.target_model_name = model_name or DEFAULT_MODEL
        self.created_at = datetime.now()
        self.execution_count = 0
        self.model = self._init_model()
        
        logger.info(f"初始化Agent: {self.name} (Model: {self.target_model_name})")
    
    def _init_model(self):
        """初始化模型"""
        # 配置真实的大模型API
        if DASHSCOPE_API_KEY or OPENAI_API_KEY:
            try:
                # 根据API密钥类型选择模型
                if DASHSCOPE_API_KEY:
                    from agentscope.model import DashScopeChatModel
                    model = DashScopeChatModel(
                        model_name=self.target_model_name,
                        api_key=DASHSCOPE_API_KEY,
                        generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化DashScope模型: {self.target_model_name}")
                    return model
                else:
                    from agentscope.model import OpenAIChatModel
                    model = OpenAIChatModel(
                        model_name=self.target_model_name,
                        api_key=OPENAI_API_KEY,
                        generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化OpenAI模型: {self.target_model_name}")
                    return model
                
            except Exception as e:
                logger.error(f"[{self.name}] 初始化真实模型失败: {e}")
                # 不抛出异常，允许降级到 Mock 或无模型模式
                return None
        else:
            logger.warning(f"[{self.name}] 未配置API密钥，使用离线分析")
            return None
    
    async def call_llm_with_retry(self, messages: List[Dict[str, str]], max_retries: int = 3, initial_delay: float = 2.0):
        """
        调用LLM，带有信号量控制和指数退避重试机制
        
        Args:
            messages: 提示词列表
            max_retries: 最大重试次数
            initial_delay: 初始延迟秒数
        """
        if not self.model:
            raise RuntimeError(f"Agent {self.name} 未初始化模型")

        async with GLOBAL_LLM_SEMAPHORE:
            for attempt in range(max_retries + 1):
                try:
                    # 调用原始模型接口
                    # 注意：AgentScope 模型可能是同步的，也可能是异步的，这里做兼容处理
                    if asyncio.iscoroutinefunction(self.model):
                        response = await self.model(messages)
                    else:
                        # 如果是同步调用，将其包装在线程中运行，避免阻塞事件循环
                        response = await asyncio.to_thread(self.model, messages)
                    
                    # 简单检查响应是否有效（AgentScope通常返回对象）
                    # 如果响应包含错误码，手动抛出异常以触发重试
                    if hasattr(response, 'status_code') and response.status_code == 429:
                         raise RuntimeError(f"Rate Limit Exceeded: {response}")
                         
                    return response
                    
                except Exception as e:
                    is_last_attempt = attempt == max_retries
                    error_msg = str(e).lower()
                    
                    # 检查是否为限流错误 (Rate Limit / Throttling)
                    is_rate_limit = "429" in error_msg or "throttling" in error_msg or "rate limit" in error_msg
                    
                    if is_rate_limit and not is_last_attempt:
                        delay = initial_delay * (2 ** attempt)  # 指数退避: 2s, 4s, 8s
                        logger.warning(f"[{self.name}] API限流，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(delay)
                    elif not is_last_attempt and "timeout" in error_msg:
                        delay = initial_delay * (2 ** attempt)
                        logger.warning(f"[{self.name}] API超时，{delay}秒后重试 ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(delay)
                    else:
                        if is_last_attempt:
                            logger.error(f"[{self.name}] LLM调用彻底失败: {e}")
                        raise e

    async def _process_model_response(self, response):
        """处理模型响应，支持流式和非流式响应"""
        if hasattr(response, '__aiter__'):
            # 处理流式响应 - 使用列表存储分块内容避免重复累积
            content_parts = []
            last_content = ""
            
            async for chunk in response:
                current_content = ""
                
                if hasattr(chunk, 'content'):
                    # 处理 ChatResponse 对象，content 可能是列表
                    content_value = chunk.content
                    if isinstance(content_value, list):
                        for item in content_value:
                            if isinstance(item, dict) and 'text' in item:
                                current_content += item['text']
                            else:
                                current_content += str(item)
                    else:
                        current_content += str(content_value)
                elif hasattr(chunk, 'text'):
                    current_content += chunk.text
                elif isinstance(chunk, str):
                    current_content += chunk
                else:
                    current_content += str(chunk)
                
                # 检查当前内容是否为上次内容的扩展
                if current_content.startswith(last_content):
                    # 提取新增部分
                    new_content = current_content[len(last_content):]
                    if new_content:
                        content_parts.append(new_content)
                else:
                    # 如果不是扩展，直接添加
                    if current_content:
                        content_parts.append(current_content)
                
                last_content = current_content
            
            # 合并所有分块内容
            return "".join(content_parts)
        elif hasattr(response, 'text'):
            # 处理非流式响应
            return response.text
        elif hasattr(response, '__dict__'):
            # 如果是SimpleNamespace或其他对象，优先使用text属性或转换为dict获取text
            if 'text' in response.__dict__:
                return response.__dict__['text']
            else:
                # 如果没有text属性，返回对象的字符串表示
                return str(response)
        else:
            # 如果response没有__dict__属性，尝试其他方法
            if hasattr(response, 'text'):
                return response.text
            else:
                return str(response)

    def reply(self, x: dict = None) -> dict:
        """AgentScope 要求的 reply 方法"""
        # 这里只是一个占位符，实际逻辑由具体 Agent 实现
        return x
