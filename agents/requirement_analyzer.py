from agents.base_agent import BaseAgent
from typing import Dict, List, Any
import json
import logging

logger = logging.getLogger(__name__)

class RequirementAnalyzerAgent(BaseAgent):
    """需求分析Agent - 分析需求的可行性和完整性"""
    
    def __init__(self, name: str, model_config_name: str):
        super().__init__(name=name, model_config_name=model_config_name)
    
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
        
        if not getattr(self, "model", None):
            return {
                "feasibility_analysis": "技术可行；建议控制范围与复杂度，分阶段交付",
                "requirements": requirements
            }
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return {"feasibility_analysis": content, "requirements": requirements}
    
    async def refine_requirements(self, requirements: Dict[str, Any], validation_issues: List[str]) -> Dict[str, Any]:
        """根据验证问题修复需求"""
        logger.info(f"[{self.name}] 根据验证反馈修复需求")
        
        prompt = f"""
        基于以下需求和验证发现的严重问题，请修复并完善需求：
        
        原始需求：
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        发现的问题：
        {chr(10).join(f'- {issue}' for issue in validation_issues)}
        
        请直接输出修复后的完整需求JSON结构，保持原有字段（functional_requirements, non_functional_requirements等），
        并确保所有问题都已解决。不要包含markdown格式标记。
        """
        
        if not getattr(self, "model", None):
             # 离线模式简单模拟修复
             requirements["refinement_note"] = "已根据验证反馈进行模拟修复"
             return requirements
             
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                refined_reqs = json.loads(json_match.group())
                # 确保关键字段存在
                if "functional_requirements" not in refined_reqs:
                    refined_reqs["functional_requirements"] = requirements.get("functional_requirements", [])
                return refined_reqs
        except Exception as e:
            logger.error(f"解析修复后的需求JSON失败: {e}")
            
        return requirements

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
        
        if not getattr(self, "model", None):
            return {
                "completeness_analysis": "需求分类齐全，建议补充异常与边界条件",
                "requirements": requirements
            }
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return {"completeness_analysis": content, "requirements": requirements}
    
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
        
        if not getattr(self, "model", None):
            return {
                "prioritized_requirements": "按照业务价值与依赖排序，先用户登录与订单主链",
                "requirements": requirements
            }
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return {"prioritized_requirements": content, "requirements": requirements}

    async def generate_review_points(self, requirements: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成关键评审要点及默认策略"""
        logger.info(f"[{self.name}] 生成关键评审要点及默认策略")
        
        prompt = f"""
        基于以下需求分析结果，请识别出最需要人工确认的3-5个关键决策点（Critical Decision Points）：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        筛选标准：
        1. 仅选择严重影响架构设计或业务流程的模糊点
        2. 排除常规、显而易见或低风险的确认项
        3. 聚焦于性能瓶颈、安全边界、核心业务规则的二义性
        
        对于每个决策点，请提供一个合理的“默认策略”（Default Strategy），即如果用户不进行干预，系统将采用的推荐做法。
        
        请直接返回JSON列表格式，包含 'point' (评审点描述) 和 'default' (默认策略) 两个字段。例如：
        [
            {{
                "point": "用户注册是否需要手机号验证",
                "default": "采用邮箱验证，暂不强制手机号"
            }},
            {{
                "point": "订单系统的并发量预估",
                "default": "按单机100QPS设计，支持横向扩展"
            }}
        ]
        """
        
        if not getattr(self, "model", None):
            return [
                {"point": "确认核心业务流程完整性", "default": "按通用行业标准流程实现"},
                {"point": "确认性能指标要求", "default": "响应时间<1s，支持100并发用户"},
                {"point": "确认安全合规要求", "default": "实现基础的用户认证与鉴权"}
            ]
            
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        # Parse JSON from content
        try:
            # Extract JSON list if embedded in text
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            # 兼容旧格式解析
            lines = [line.strip().lstrip('- ').lstrip('1. ') for line in content.split('\n') if line.strip()]
            return [{"point": line, "default": "未指定默认策略"} for line in lines[:5]]
        except Exception as e:
            logger.warning(f"解析评审要点失败: {e}")
            return [{"point": content, "default": "未指定默认策略"}]
