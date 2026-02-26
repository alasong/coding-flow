import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from agentscope.agent import AgentBase
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL, BACKUP_MODELS

logger = logging.getLogger(__name__)

# 全局信号量，控制所有Agent的总并发请求数，避免触发API限流
GLOBAL_LLM_SEMAPHORE = asyncio.Semaphore(3)

class BaseAgent(AgentBase):
    """Agent基类 - 所有Agent的抽象基类"""
    
    def __init__(self, name: str, model_config_name: str, model_name: str = None, **kwargs):
        """
        初始化Agent基类
        """
        super().__init__()
        self.name = name
        self.model_config_name = model_config_name
        self.target_model_name = model_name or DEFAULT_MODEL
        self.created_at = datetime.now()
        self.execution_count = 0
        self.model = self._init_model(self.target_model_name)
        
        logger.info(f"初始化Agent: {self.name} (Model: {self.target_model_name})")
    
    def _init_model(self, model_name):
        """初始化指定名称的模型"""
        # 配置真实的大模型API
        if DASHSCOPE_API_KEY or OPENAI_API_KEY:
            try:
                # 根据API密钥类型选择模型
                if DASHSCOPE_API_KEY:
                    from agentscope.model import DashScopeChatModel
                    model = DashScopeChatModel(
                        model_name=model_name,
                        api_key=DASHSCOPE_API_KEY,
                        generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
                    )
                    return model
                else:
                    from agentscope.model import OpenAIChatModel
                    model = OpenAIChatModel(
                        model_name=model_name,
                        api_key=OPENAI_API_KEY,
                        generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
                    )
                    return model
            except Exception as e:
                logger.error(f"[{self.name}] 初始化真实模型失败 ({model_name}): {e}")
                return None
        else:
            return None
    
    async def call_llm_with_retry(self, messages: List[Dict[str, str]], max_retries: int = 3, initial_delay: float = 2.0):
        """
        调用LLM，带有信号量控制、指数退避重试和模型降级机制
        """
        if not self.model:
            raise RuntimeError(f"Agent {self.name} 未初始化模型")

        # 候选模型列表：主模型 + 备用模型池
        # 优化：每次调用都重新初始化备用模型可能开销较大，且模型对象本身是无状态的（配置除外），
        # 但为了简单起见，且 AgentScope 模型初始化通常只是配置参数，这里暂保持现状。
        # 重点：确保模型对象正确初始化
        candidate_models = []
        if self.model:
             candidate_models.append(self.model)
        
        # 初始化备用模型
        if BACKUP_MODELS:
            for backup_name in BACKUP_MODELS:
                if backup_name != self.target_model_name:
                    backup_model = self._init_model(backup_name)
                    if backup_model:
                        candidate_models.append(backup_model)
        
        if not candidate_models:
             raise RuntimeError(f"Agent {self.name} 没有可用的模型")

        async with GLOBAL_LLM_SEMAPHORE:
            last_error = None
            
            # 尝试每个候选模型
            for model_idx, current_model in enumerate(candidate_models):
                
                # 对当前模型进行重试
                for attempt in range(max_retries + 1):
                    try:
                        # 快速测试（仅在首次使用备用模型时，或者为了快速失败）
                        # 这里我们直接发起请求，因为请求本身就是测试
                        
                        # 尝试判断 __call__ 是否是协程函数
                        try:
                            # 针对 AgentScope 的兼容性处理
                            is_async = asyncio.iscoroutinefunction(current_model.__call__)
                        except:
                            is_async = False
                            
                        if is_async:
                            response = await current_model(messages)
                        else:
                            response = await asyncio.to_thread(current_model, messages)
                            if asyncio.iscoroutine(response):
                                response = await response
                        
                        # 检查限流状态码
                        if hasattr(response, 'status_code') and response.status_code == 429:
                             raise RuntimeError(f"Rate Limit Exceeded: {response}")
                             
                        # 如果成功，直接返回
                        return response
                        
                    except Exception as e:
                        last_error = e
                        error_msg = str(e).lower()
                        is_rate_limit = "429" in error_msg or "throttling" in error_msg or "rate limit" in error_msg
                        
                        if is_rate_limit:
                            if attempt < max_retries:
                                delay = initial_delay * (2 ** attempt)
                                logger.warning(f"[{self.name}] API限流 (Model {model_idx}), {delay}s后重试...")
                                await asyncio.sleep(delay)
                            else:
                                logger.warning(f"[{self.name}] Model {model_idx} 限流重试耗尽，尝试下一个备用模型...")
                                break # 跳出当前模型的重试循环，进入下一个模型
                        else:
                            # 非限流错误，直接抛出或重试
                            if attempt < max_retries:
                                await asyncio.sleep(initial_delay)
                            else:
                                # 如果是非限流错误（如参数错误、网络断开），通常换模型也不一定能解决，
                                # 但为了鲁棒性，如果是备用模型，我们还是可以尝试下一个。
                                # 如果是主模型出错且非限流，可能需要更谨慎。
                                # 这里简化策略：只要出错且重试耗尽，就换模型
                                logger.warning(f"[{self.name}] Model {model_idx} 调用失败: {e}，尝试下一个备用模型...")
                                break

            # 所有模型都失败了
            logger.error(f"[{self.name}] 所有可用模型均调用失败。Last error: {last_error}")
            raise last_error

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
