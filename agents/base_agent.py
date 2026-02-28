import logging
import asyncio
import json
import re
import os as _os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from agentscope.agent import AgentBase
from config import (
    DASHSCOPE_API_KEY, OPENAI_API_KEY, SILICONFLOW_API_KEY, 
    SILICONFLOW_BASE_URL, SILICONFLOW_DEFAULT_MODEL,
    DEFAULT_MODEL, BACKUP_MODELS, LLMConfig,
    LLM_PROVIDER_PRIORITY, PROVIDER_DEFAULT_MODELS
)

logger = logging.getLogger(__name__)

# 全局信号量，控制所有Agent的总并发请求数，避免触发API限流
GLOBAL_LLM_SEMAPHORE = asyncio.Semaphore(LLMConfig.CONCURRENT_LIMIT)


def get_available_providers() -> List[str]:
    """获取可用的 LLM 平台列表（按优先级排序）"""
    available = []
    if SILICONFLOW_API_KEY:
        available.append("siliconflow")
    if DASHSCOPE_API_KEY:
        available.append("dashscope")
    if OPENAI_API_KEY:
        available.append("openai")
    
    # 按配置的优先级排序
    result = []
    for provider in LLM_PROVIDER_PRIORITY:
        if provider in available:
            result.append(provider)
    
    # 添加未在优先级列表中但可用的平台
    for provider in available:
        if provider not in result:
            result.append(provider)
    
    return result


def _get_default_model_for_provider(provider: str = None) -> str:
    """根据平台获取对应的默认模型"""
    if provider is None:
        # 获取第一个可用平台
        providers = get_available_providers()
        if providers:
            provider = providers[0]
    
    if provider and provider in PROVIDER_DEFAULT_MODELS:
        return PROVIDER_DEFAULT_MODELS[provider]
    return DEFAULT_MODEL


class BaseAgent(AgentBase):
    """Agent基类 - 所有Agent的抽象基类"""
    
    def __init__(
        self, 
        name: str, 
        model_config_name: str, 
        model_name: str = None,
        task_type: str = "default",
        **kwargs
    ):
        """
        初始化Agent基类
        
        Args:
            name: Agent 名称
            model_config_name: 模型配置名称
            model_name: 模型名称（可选，默认根据平台自动选择）
            task_type: 任务类型，影响生成参数
                - "precision": 精确性任务（分析、验证）
                - "creativity": 创造性任务（生成、创作）
                - "long": 长文档任务
                - "medium": 中等长度任务
                - "default": 默认参数
        """
        super().__init__()
        self.name = name
        self.model_config_name = model_config_name
        self.task_type = task_type
        self.created_at = datetime.now()
        self.execution_count = 0
        
        # 获取可用平台
        self.available_providers = get_available_providers()
        
        # 如果未指定模型，使用第一个可用平台的默认模型
        self.target_model_name = model_name
        if not self.target_model_name and self.available_providers:
            self.target_model_name = _get_default_model_for_provider(self.available_providers[0])
        
        # 初始化模型（使用第一个可用平台）
        self.model = None
        self.current_provider = None
        if self.available_providers:
            self.current_provider = self.available_providers[0]
            self.model = self._init_model_for_provider(self.target_model_name, self.current_provider)
        
        logger.info(f"初始化Agent: {self.name} (Model: {self.target_model_name}, Provider: {self.current_provider}, TaskType: {task_type})")
    
    def _init_model_for_provider(self, model_name: str, provider: str):
        """
        为指定平台初始化模型
        
        Args:
            model_name: 模型名称
            provider: 平台名称 (siliconflow/dashscope/openai)
        """
        generate_kwargs = LLMConfig.get_generate_kwargs(self.task_type)
        
        try:
            if provider == "siliconflow":
                from agentscope.model import OpenAIChatModel
                # 设置环境变量让 OpenAI 客户端使用硅基流动的 base_url
                original_base_url = _os.environ.get("OPENAI_BASE_URL")
                _os.environ["OPENAI_BASE_URL"] = SILICONFLOW_BASE_URL
                try:
                    model = OpenAIChatModel(
                        model_name=model_name,
                        api_key=SILICONFLOW_API_KEY,
                        generate_kwargs=generate_kwargs
                    )
                    logger.debug(f"[{self.name}] 初始化硅基流动模型: {model_name}")
                    return model
                finally:
                    if original_base_url:
                        _os.environ["OPENAI_BASE_URL"] = original_base_url
                    else:
                        _os.environ.pop("OPENAI_BASE_URL", None)
                        
            elif provider == "dashscope":
                from agentscope.model import DashScopeChatModel
                model = DashScopeChatModel(
                    model_name=model_name,
                    api_key=DASHSCOPE_API_KEY,
                    generate_kwargs=generate_kwargs
                )
                logger.debug(f"[{self.name}] 初始化 DashScope 模型: {model_name}")
                return model
                
            elif provider == "openai":
                from agentscope.model import OpenAIChatModel
                model = OpenAIChatModel(
                    model_name=model_name,
                    api_key=OPENAI_API_KEY,
                    generate_kwargs=generate_kwargs
                )
                logger.debug(f"[{self.name}] 初始化 OpenAI 模型: {model_name}")
                return model
                
        except Exception as e:
            logger.error(f"[{self.name}] 初始化 {provider} 模型失败 ({model_name}): {e}")
            return None
        
        return None
    
    async def call_llm_with_retry(
        self, 
        messages: List[Dict[str, str]], 
        max_retries: int = None, 
        initial_delay: float = None
    ):
        """
        调用LLM，带有信号量控制、指数退避重试和跨平台降级机制
        """
        if max_retries is None:
            max_retries = LLMConfig.MAX_RETRIES
        if initial_delay is None:
            initial_delay = LLMConfig.RETRY_DELAY
            
        if not self.available_providers:
            raise RuntimeError(f"Agent {self.name} 没有可用的 LLM 平台")

        async with GLOBAL_LLM_SEMAPHORE:
            last_error = None
            
            # 按平台优先级尝试
            for provider_idx, provider in enumerate(self.available_providers):
                # 获取该平台的模型
                model_name = _get_default_model_for_provider(provider)
                model = self._init_model_for_provider(model_name, provider)
                
                if not model:
                    logger.warning(f"[{self.name}] 平台 {provider} 初始化失败，尝试下一个...")
                    continue
                
                logger.info(f"[{self.name}] 尝试平台 {provider} (模型: {model_name})")
                
                # 对当前模型进行重试
                for attempt in range(max_retries + 1):
                    try:
                        is_async = asyncio.iscoroutinefunction(model.__call__)
                        
                        if is_async:
                            response = await model(messages)
                        else:
                            response = await asyncio.to_thread(model, messages)
                            if asyncio.iscoroutine(response):
                                response = await response
                        
                        # 检查限流状态码
                        if hasattr(response, 'status_code') and response.status_code == 429:
                            raise RuntimeError(f"Rate Limit Exceeded")
                            
                        # 成功，更新当前平台并返回
                        self.current_provider = provider
                        self.target_model_name = model_name
                        return response
                        
                    except Exception as e:
                        last_error = e
                        error_msg = str(e).lower()
                        is_rate_limit = "429" in error_msg or "throttling" in error_msg or "rate limit" in error_msg
                        
                        if is_rate_limit:
                            if attempt < max_retries:
                                delay = initial_delay * (2 ** attempt)
                                logger.warning(f"[{self.name}] {provider} 限流，{delay}s 后重试...")
                                await asyncio.sleep(delay)
                            else:
                                logger.warning(f"[{self.name}] {provider} 限流重试耗尽，尝试下一个平台...")
                                break  # 跳出重试循环，尝试下一个平台
                        else:
                            if attempt < max_retries:
                                await asyncio.sleep(initial_delay)
                            else:
                                logger.warning(f"[{self.name}] {provider} 调用失败: {e}，尝试下一个平台...")
                                break  # 跳出重试循环，尝试下一个平台

            # 所有平台都失败了
            logger.error(f"[{self.name}] 所有平台均调用失败。Last error: {last_error}")
            raise last_error

    async def _process_model_response(self, response):
        """处理模型响应，支持流式和非流式响应"""
        if hasattr(response, '__aiter__'):
            # 处理流式响应
            content_parts = []
            last_content = ""
            
            async for chunk in response:
                current_content = ""
                
                if hasattr(chunk, 'content'):
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
                
                if current_content.startswith(last_content):
                    new_content = current_content[len(last_content):]
                    if new_content:
                        content_parts.append(new_content)
                else:
                    if current_content:
                        content_parts.append(current_content)
                
                last_content = current_content
            
            return "".join(content_parts)
        elif hasattr(response, 'text'):
            return response.text
        elif hasattr(response, '__dict__'):
            if 'text' in response.__dict__:
                return response.__dict__['text']
            else:
                return str(response)
        else:
            if hasattr(response, 'text'):
                return response.text
            else:
                return str(response)

    def _extract_json(self, content: str, expected_type: type = dict) -> Optional[Any]:
        """提取并解析 JSON"""
        if not content:
            return None
            
        try:
            # 预处理：移除注释
            content = re.sub(r'(?m)^\s*//.*', '', content)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            content = re.sub(r',(\s*[}\]])', r'\1', content)

            # 尝试提取代码块中的 JSON
            for pattern in [r'```json\s*([\s\S]*?)\s*```', r'```\s*([\s\S]*?)\s*```']:
                match = re.search(pattern, content)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        continue

            # 尝试提取 JSON 对象或数组
            if expected_type == list:
                match = re.search(r'\[[\s\S]*\]', content)
            else:
                match = re.search(r'\{[\s\S]*\}', content)

            if match:
                return json.loads(match.group(0))

            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"[{self.name}] JSON 提取异常: {e}")
            return None

    def reply(self, x: dict = None) -> dict:
        """AgentScope 要求的 reply 方法"""
        return x
