from agentscope.agent import AgentBase
from agentscope.message import Msg
from typing import Dict, List, Any
import json
import logging
from datetime import datetime
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class RequirementCollectorAgent(AgentBase):
    """需求收集Agent - 负责收集和整理用户需求"""
    
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
                self.model = MockModel("requirement-collector")
        else:
            logger.warning(f"[{self.name}] 未配置API密钥, 使用模拟模式")
            from .mock_model import MockModel
            self.model = MockModel("requirement-collector")
        
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
    
    async def collect_requirements(self, user_input: str) -> Dict[str, Any]:
        """收集用户需求"""
        logger.info(f"[{self.name}] 开始收集需求: {user_input}")
        
        # 构建清晰的提示，要求模型返回结构化的需求
        prompt = f"""
        请分析以下用户需求，提取关键功能点和非功能需求：
        
        用户需求：{user_input}
        
        请按以下格式返回分析结果：
        
        ## 功能需求
        - 具体的功能点1
        - 具体的功能点2
        
        ## 非功能需求  
        - 性能要求
        - 安全要求
        - 可用性要求
        
        ## 约束条件
        - 技术约束
        - 业务约束
        
        重要要求：
        1. 每个功能需求只列出一次，避免重复
        2. 总共不超过20个功能需求点
        3. 每个需求点控制在50字以内
        4. 按重要程度排序，最重要的功能放在前面
        
        请确保每个需求点都简洁明了，避免重复内容。
        """
        
        # 使用AgentScope的模型调用
        response = await self.model([{"role": "user", "content": prompt}])
        
        requirements = {
            "raw_input": user_input,
            "functional_requirements": [],
            "non_functional_requirements": [],
            "constraints": [],
            "key_features": [],
            "extracted_at": datetime.now().isoformat()
        }
        
        # 处理响应
        content = await self._process_model_response(response)
        logger.debug(f"[{self.name}] 模型原始响应: {content[:500]}...")
        
        # 使用直接提取方法 - 处理格式混乱的模型输出
        lines = content.split('\n')
        seen_items = set()  # 用于去重
        
        # 直接提取所有有效的列表项
        valid_items = []
        for line in lines:
            line = line.strip()
            if line.startswith('-'):
                # 提取列表项内容
                item = line[1:].strip()
                
                # 清理和验证
                if item and len(item) >= 3:  # 最少3个字符
                    # 深度清理 - 移除各种标记和噪音
                    item = item.replace('##', '').replace('#', '').replace('**', '').strip()
                    
                    # 高级过滤 - 移除残留的标题词汇
                    if any(keyword in item for keyword in ['功能需求', '非功能需求', '约束条件', '关键功能']):
                        continue
                    
                    # 清理开头和结尾的噪音
                    item = item.strip(' -\t*')
                    
                    # 基本过滤
                    if (item and 
                        3 <= len(item) <= 150 and
                        item not in seen_items and
                        not item.isdigit() and  # 排除纯数字
                        len(item.split()) >= 1):  # 至少一个词
                        
                        seen_items.add(item)
                        valid_items.append(item)
        
        # 如果没有提取到任何有效项，尝试其他方法
        if not valid_items:
            logger.warning(f"[{self.name}] 标准解析失败，尝试备用方法")
            # 备用：提取所有非空行并清理
            for line in lines:
                line = line.strip()
                if line and len(line) >= 5 and not line.startswith('#') and line not in seen_items:
                    # 深度清理行
                    cleaned = line.replace('#', '').replace('*', '').replace('##', '').strip()
                    # 移除标题词汇
                    if any(keyword in cleaned for keyword in ['功能需求', '非功能需求', '约束条件', '关键功能']):
                        continue
                    cleaned = cleaned.strip(' -\t*')
                    
                    if (cleaned and 
                        5 <= len(cleaned) <= 150 and
                        cleaned not in seen_items and
                        not cleaned.isdigit()):
                        
                        seen_items.add(cleaned)
                        valid_items.append(cleaned)
        
        # 智能分类
        functional = []
        non_functional = []
        constraints = []
        key_features = []
        
        for item in valid_items:
            item_lower = item.lower()
              
            # 分类逻辑
            if any(keyword in item_lower for keyword in ['性能', '响应', '并发', '速度', '负载']):
                non_functional.append(item)
            elif any(keyword in item_lower for keyword in ['安全', '加密', '权限', '认证', '登录']):
                non_functional.append(item)
            elif any(keyword in item_lower for keyword in ['可用', '界面', '操作', '体验', '易用']):
                non_functional.append(item)
            elif any(keyword in item_lower for keyword in ['技术', '架构', '平台', '框架', '环境']):
                constraints.append(item)
            elif any(keyword in item_lower for keyword in ['重要', '关键', '核心', '主要']):
                key_features.append(item)
            else:
                functional.append(item)
        
        # 设置最终需求
        requirements["functional_requirements"] = functional[:15]  # 限制功能需求数量
        requirements["non_functional_requirements"] = non_functional
        requirements["constraints"] = constraints
        requirements["key_features"] = key_features or functional[:5]  # 如果没有关键功能，用功能需求的前5个
        
        # 限制功能需求数量，避免过多
        requirements["functional_requirements"] = requirements["functional_requirements"][:15]
        
        # 如果没有提取到关键功能，从功能需求中提取
        if not requirements["key_features"] and requirements["functional_requirements"]:
            # 提取前5个功能作为主要功能点
            requirements["key_features"] = requirements["functional_requirements"][:5]
        
        logger.info(f"[{self.name}] 需求收集完成，发现 {len(requirements['functional_requirements'])} 个功能需求，{len(requirements['non_functional_requirements'])} 个非功能需求")
        return requirements
    
    def _parse_requirements(self, content: str) -> Dict[str, Any]:
        """解析需求内容"""
        requirements = {
            "functional_requirements": [],
            "non_functional_requirements": [],
            "business_requirements": [],
            "user_requirements": [],
            "technical_requirements": []
        }
        
        # 简单的解析逻辑，可以根据需要改进
        lines = content.split('\n')
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if '功能需求' in line or '1.' in line:
                current_category = "functional_requirements"
            elif '非功能需求' in line or '2.' in line:
                current_category = "non_functional_requirements"
            elif '业务需求' in line or '3.' in line:
                current_category = "business_requirements"
            elif '用户需求' in line or '4.' in line:
                current_category = "user_requirements"
            elif '技术需求' in line or '5.' in line:
                current_category = "technical_requirements"
            elif current_category and line.startswith('-'):
                requirements[current_category].append(line[1:].strip())
        
        return requirements
    
    async def clarify_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """澄清和补充需求"""
        prompt = f"""
        基于以下收集到的需求，请识别需要进一步澄清的地方：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        请提出具体的澄清问题，帮助用户更准确地描述他们的需求。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        
        return {
            "clarification_questions": response.text if hasattr(response, 'text') else str(response),
            "original_requirements": requirements
        }