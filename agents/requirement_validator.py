from agentscope.agent import AgentBase
from agentscope.message import Msg
from typing import Dict, List, Any
import json
import logging
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class RequirementValidatorAgent(AgentBase):
    """需求验证Agent - 验证需求的完整性和一致性"""
    
    def __init__(self, name: str, model_config_name: str):
        super().__init__()
        self.name = name
        self.model_config_name = model_config_name
        
        # 配置真实的大模型API
        if DASHSCOPE_API_KEY or OPENAI_API_KEY:
            try:
                # 根据API密钥类型选择模型
                if DASHSCOPE_API_KEY:
                    from agentscope.model import DashScopeChatModel
                    self.model = DashScopeChatModel(
                        model_name="qwen-turbo",
                        api_key=DASHSCOPE_API_KEY,
                        generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化DashScope模型: qwen-turbo")
                else:
                    from agentscope.model import OpenAIChatModel
                    self.model = OpenAIChatModel(
                        model_name=DEFAULT_MODEL,
                        api_key=OPENAI_API_KEY,
                        generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化OpenAI模型: {DEFAULT_MODEL}")
                
            except Exception as e:
                logger.warning(f"[{self.name}] 初始化真实模型失败: {e}, 使用模拟模式")
                from .mock_model import MockModel
                self.model = MockModel("requirement-validator")
        else:
            logger.warning(f"[{self.name}] 未配置API密钥, 使用模拟模式")
            from .mock_model import MockModel
            self.model = MockModel("requirement-validator")
    
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
        else:
            return str(response)
    
    async def validate_correctness(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证需求的正确性和完整性"""
        logger.info(f"[{self.name}] 开始验证需求正确性")
        
        # 使用AgentScope的模型调用
        prompt = f"""
        请验证以下需求的正确性和完整性：
        
        功能需求：{requirements.get('functional_requirements', [])}
        非功能需求：{requirements.get('non_functional_requirements', [])}
        约束条件：{requirements.get('constraints', [])}
        
        请从以下方面进行验证：
        1. 需求完整性（是否缺少关键需求）
        2. 需求一致性（是否存在矛盾）
        3. 需求可测试性（是否可以验证）
        4. 提供改进建议
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        
        # 处理响应
        content = await self._process_model_response(response)
        
        return {
            "validation_results": content,
            "requirements": requirements
        }
    
    async def validate_completeness(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证需求的完整性"""
        prompt = f"""
        请验证以下需求的完整性：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        请检查：
        1. 是否包含所有必要的需求类型
        2. 每个需求是否完整描述
        3. 是否缺少关键信息
        4. 需求的粒度是否合适
        5. 是否有遗漏的需求
        
        请提供完整性验证结果。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        
        return {
            "completeness_validation": response.text if hasattr(response, 'text') else str(response),
            "requirements": requirements
        }
    
    async def validate_consistency(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证需求的一致性"""
        prompt = f"""
        请验证以下需求的一致性：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        请检查：
        1. 需求之间是否存在冲突
        2. 需求是否有重复
        3. 需求的术语是否一致
        4. 需求的优先级是否一致
        5. 需求的标准是否一致
        
        请提供一致性验证结果。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        
        return {
            "consistency_validation": response.text if hasattr(response, 'text') else str(response),
            "requirements": requirements
        }
    
    async def generate_test_cases(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """基于需求生成测试用例"""
        prompt = f"""
        请基于以下需求生成测试用例：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        请为每个功能需求生成相应的测试用例，包括：
        1. 测试场景描述
        2. 输入数据
        3. 预期结果
        4. 测试类型（功能测试、性能测试、安全测试等）
        5. 测试优先级
        
        请提供详细的测试用例列表。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        
        return {
            "test_cases": response.text if hasattr(response, 'text') else str(response),
            "requirements": requirements
        }