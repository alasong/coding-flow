"""需求收集Agent - 负责收集和整理用户需求"""

from agents.base_agent import BaseAgent
from agentscope.message import Msg
from typing import Dict, List, Any
import json
import logging
from datetime import datetime
from config import DEFAULT_MODEL

logger = logging.getLogger(__name__)


class RequirementCollectorAgent(BaseAgent):
    """需求收集Agent - 负责收集和整理用户需求"""
    
    def __init__(self, name: str = "需求收集专家", model_config_name: str = "requirement_collector"):
        super().__init__(
            name=name,
            model_config_name=model_config_name,
            model_name=DEFAULT_MODEL,
            task_type="creativity"
        )
    
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
        
        # 使用模型调用
        if not getattr(self, "model", None):
            # 离线解析：按行拆分并用关键词分类
            return self._offline_parse_requirements(user_input)
        
        response = await self.call_llm_with_retry([{"role": "user", "content": prompt}])
        
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
        valid_items = self._extract_valid_items(content)
        
        # 智能分类
        functional, non_functional, constraints, key_features = self._classify_items(valid_items)
        
        # 设置最终需求
        requirements["functional_requirements"] = functional[:15]
        requirements["non_functional_requirements"] = non_functional
        requirements["constraints"] = constraints
        requirements["key_features"] = key_features or functional[:5]
        
        logger.info(f"[{self.name}] 需求收集完成，发现 {len(requirements['functional_requirements'])} 个功能需求，{len(requirements['non_functional_requirements'])} 个非功能需求")
        return requirements
    
    def _offline_parse_requirements(self, user_input: str) -> Dict[str, Any]:
        """离线解析需求"""
        text = user_input
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        tokens = []
        for l in lines:
            for t in l.replace('，', ' ').replace(',', ' ').split():
                if len(t) >= 2:
                    tokens.append(t)
        functional = []
        non_functional = []
        constraints = []
        key_features = []
        for item in tokens:
            low = item.lower()
            if any(k in low for k in ['性能', '并发', '响应', 'latency', 'qps']):
                non_functional.append(item)
            elif any(k in low for k in ['安全', '认证', '授权', '加密', 'security']):
                non_functional.append(item)
            elif any(k in low for k in ['约束', '限制', '平台', '框架']):
                constraints.append(item)
            else:
                functional.append(item)
        return {
            "raw_input": user_input,
            "functional_requirements": functional[:15],
            "non_functional_requirements": non_functional,
            "constraints": constraints,
            "key_features": key_features or functional[:5],
            "extracted_at": datetime.now().isoformat()
        }
    
    def _extract_valid_items(self, content: str) -> List[str]:
        """从内容中提取有效的列表项"""
        lines = content.split('\n')
        seen_items = set()
        valid_items = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('-'):
                item = line[1:].strip()
                
                if item and len(item) >= 3:
                    item = item.replace('##', '').replace('#', '').replace('**', '').strip()
                    
                    if any(keyword in item for keyword in ['功能需求', '非功能需求', '约束条件', '关键功能']):
                        continue
                    
                    item = item.strip(' -\t*')
                    
                    if (item and 
                        3 <= len(item) <= 150 and
                        item not in seen_items and
                        not item.isdigit() and
                        len(item.split()) >= 1):
                        
                        seen_items.add(item)
                        valid_items.append(item)
        
        # 如果没有提取到任何有效项，尝试备用方法
        if not valid_items:
            for line in lines:
                line = line.strip()
                if line and len(line) >= 5 and not line.startswith('#') and line not in seen_items:
                    cleaned = line.replace('#', '').replace('*', '').replace('##', '').strip()
                    if any(keyword in cleaned for keyword in ['功能需求', '非功能需求', '约束条件', '关键功能']):
                        continue
                    cleaned = cleaned.strip(' -\t*')
                    
                    if (cleaned and 
                        5 <= len(cleaned) <= 150 and
                        cleaned not in seen_items and
                        not cleaned.isdigit()):
                        
                        seen_items.add(cleaned)
                        valid_items.append(cleaned)
        
        return valid_items
    
    def _classify_items(self, valid_items: List[str]) -> tuple:
        """智能分类需求项"""
        functional = []
        non_functional = []
        constraints = []
        key_features = []
        
        for item in valid_items:
            item_lower = item.lower()
            
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
        
        return functional, non_functional, constraints, key_features
    
    async def clarify_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """澄清和补充需求"""
        prompt = f"""
        基于以下收集到的需求，请识别需要进一步澄清的地方：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        请提出具体的澄清问题，帮助用户更准确地描述他们的需求。
        """
        
        response = await self.call_llm_with_retry([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        return {
            "clarification_questions": content,
            "original_requirements": requirements
        }
