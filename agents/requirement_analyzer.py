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
        
        请以 JSON 格式返回分析结果，包含以下字段：
        - feasibility_score: 可行性评分 (0-100)
        - technical_risks: [str] 技术风险列表
        - resource_requirements: [str] 资源需求列表
        - conclusion: 总体结论
        - analysis_detail: 详细分析说明
        """
        
        if not getattr(self, "model", None):
             return {
                "feasibility_score": 80,
                "technical_risks": ["技术选型适配性", "数据一致性保障"],
                "resource_requirements": ["建议根据实际规模评估团队配置"],
                "conclusion": "总体可行，建议进行详细技术预研"
            }
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        # 尝试提取 JSON
        analysis_result = self._extract_json(content)
        if analysis_result:
             return {"feasibility_analysis": analysis_result, "requirements": requirements}
        else:
             return {"feasibility_analysis": content, "requirements": requirements}

    def _extract_json(self, content: str, expected_type=dict):
        """提取并解析结构化数据 (优先尝试YAML，降级尝试JSON)"""
        import yaml
        import re
        
        try:
            # 0. 预处理：移除注释
            content = re.sub(r'(?m)^\s*//.*', '', content)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

            # 1. 尝试提取YAML代码块
            code_block_match_yaml = re.search(r'```yaml\s*([\s\S]*?)\s*```', content)
            if code_block_match_yaml:
                try:
                    return yaml.safe_load(code_block_match_yaml.group(1))
                except:
                    pass

            # 2. 尝试提取JSON代码块
            code_block_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if code_block_match:
                try:
                    # 先尝试当JSON解析
                    return json.loads(code_block_match.group(1))
                except:
                    try:
                        # 失败则尝试当YAML解析（JSON是YAML的子集）
                        return yaml.safe_load(code_block_match.group(1))
                    except:
                        pass

            # 3. 尝试通用代码块
            code_block_match_2 = re.search(r'```\s*([\s\S]*?)\s*```', content)
            if code_block_match_2:
                raw_str = code_block_match_2.group(1)
                try:
                    return yaml.safe_load(raw_str)
                except:
                    pass

            # 4. 直接尝试解析全文
            try:
                parsed = yaml.safe_load(content)
                if isinstance(parsed, (dict, list)):
                    return parsed
            except:
                pass
            
            # 5. 尝试JSON降级解析（处理不规范JSON）
            try:
                # 修复末尾逗号
                fixed_content = re.sub(r',(\s*[}\]])', r'\1', content)
                return json.loads(fixed_content)
            except:
                pass

            return None
            
        except Exception as e:
            logger.error(f"提取结构化数据失败: {e}")
            logger.debug(f"原始内容: {content[:500]}...")
            return None
            
    async def refine_requirements(self, requirements: Dict[str, Any], validation_issues: List[str], history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """根据验证问题修复需求"""
        logger.info(f"[{self.name}] 根据验证反馈修复需求")
        
        # 构建历史记录文本
        history_text = ""
        if history and len(history) > 0:
            history_text = "\n【历史修复尝试（失败）】\n"
            for h in history[-3:]: # 只看最近3次
                history_text += f"- 第{h.get('loop')}次循环尝试解决的问题: {h.get('issues')}\n"
            history_text += "\n注意：请避免重复上述失败的修复策略。如果发现某些约束无法同时满足（例如：不进行身份认证 vs 需要数据安全），请进行权衡（Trade-off），修改其中一项约束以消除冲突，或者明确标注该冲突需人工决策。\n"

        prompt = f"""
        基于以下需求和验证发现的严重问题，请修复并完善需求。
        
        原始需求：
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        当前发现的问题：
        {chr(10).join(f'- {issue}' for issue in validation_issues)}
        
        {history_text}

        请执行以下步骤（思维链）：
        1. **分析问题根源**：针对每个问题，分析是描述不清、逻辑冲突还是技术不可行？
        2. **制定修复策略**：
           - 如果是逻辑冲突（如安全 vs 便捷），明确选择一个优先方向（Trade-off）。
           - 如果是描述模糊，补充具体的量化指标（如 "高性能" -> "响应时间<500ms"）。
           - 如果是信息缺失，根据通用行业标准进行合理假设补充。
        3. **执行修复**：修改需求内容。
        4. **自我检查**：确保修复后的需求不会引入新的冲突。
        
        请直接输出修复后的完整需求，使用 **YAML格式**。
        保持原有字段（functional_requirements, non_functional_requirements等）。
        不要包含markdown格式标记，直接输出YAML内容。
        """
        
        if not getattr(self, "model", None):
             # 离线模式简单模拟修复
             requirements["refinement_note"] = "已根据验证反馈进行模拟修复"
             return requirements
             
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        refined_reqs = self._extract_json(content)
        if refined_reqs:
            # 确保关键字段存在
            if "functional_requirements" not in refined_reqs:
                refined_reqs["functional_requirements"] = requirements.get("functional_requirements", [])
            return refined_reqs
        else:
            logger.error(f"解析修复后的需求JSON失败")
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
                "prioritized_requirements": "建议优先实现核心业务流程与高风险模块。基于业务价值与技术复杂度排序。",
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
        1. 仅选择严重影响架构设计或业务流程的模糊点。
        2. 排除常规、显而易见或低风险的确认项。
        3. 聚焦于性能瓶颈、安全边界、核心业务规则的二义性。
        
        对于每个决策点，请提供一个合理的“默认策略”（Default Strategy），即如果用户不进行干预，系统将采用的推荐做法。
        
        请直接返回JSON列表格式，包含 'point' (评审点描述) 和 'default' (默认策略) 两个字段。
        不要使用特定的业务作为示例，请根据实际输入的需求生成。
        """
        
        if not getattr(self, "model", None):
            return [
                {"point": "确认核心业务逻辑是否完整", "default": "基于通用业务实践进行补充"},
                {"point": "确认非功能性需求指标", "default": "满足常规企业级应用性能与安全标准"},
                {"point": "确认关键业务规则", "default": "采用行业通用规则或最佳实践"}
            ]
            
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        review_points = self._extract_json(content, expected_type=list)
        if review_points:
            return review_points
        else:
            # 兼容旧格式解析
            lines = [line.strip().lstrip('- ').lstrip('1. ') for line in content.split('\n') if line.strip()]
            return [{"point": line, "default": "未指定默认策略"} for line in lines[:5]]
