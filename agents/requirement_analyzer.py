from agentscope.agent import AgentBase
from agentscope.message import Msg
from typing import Dict, List, Any
import json
import logging
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class RequirementAnalyzerAgent(AgentBase):
    """需求分析Agent - 分析需求的可行性和完整性"""
    
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
                logger.error(f"[{self.name}] 初始化真实模型失败: {e}")
                raise RuntimeError(f"模型初始化失败: {e}")
        else:
            logger.error(f"[{self.name}] 未配置API密钥")
            raise RuntimeError("未配置API密钥，无法初始化模型。请在环境变量中设置DASHSCOPE_API_KEY或OPENAI_API_KEY。")
    
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
    
    async def analyze_feasibility(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析需求的可行性"""
        logger.info(f"[{self.name}] 开始分析需求可行性")
        
        prompt = f"""
        作为需求分析专家，请分析以下需求的可行性：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        请从以下维度进行分析：
        1. 技术可行性：现有技术是否能实现这些需求
        2. 经济可行性：开发成本是否合理
        3. 时间可行性：开发周期是否可接受
        4. 资源可行性：是否有足够的人力和技术资源
        5. 风险分析：潜在的技术和业务风险
        
        请提供详细的分析结果和建议。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        
        content = await self._process_model_response(response)
        
        return {
            "feasibility_analysis": content,
            "requirements": requirements
        }
    
    async def analyze_completeness(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析需求的完整性"""
        prompt = f"""
        请分析以下需求的完整性：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        请检查：
        1. 是否有遗漏的重要需求类别
        2. 每个需求是否描述完整、清晰
        3. 需求之间是否存在冲突
        4. 是否有重复的需求
        5. 需求是否可以进一步细化
        
        请提供完整性评估和改进建议。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        
        content = await self._process_model_response(response)
        return {
            "completeness_analysis": content,
            "requirements": requirements
        }
    
    async def prioritize_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """对需求进行优先级排序"""
        prompt = f"""
        请对以下需求进行优先级排序：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        请按照以下标准进行排序：
        1. 业务价值：对业务目标的重要程度
        2. 技术复杂度：实现的难易程度
        3. 用户影响：对用户的影响范围
        4. 开发成本：所需的时间和资源
        5. 风险程度：实现的风险大小
        
        请提供优先级排序结果和理由。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        return {
            "prioritized_requirements": content,
            "requirements": requirements
        }