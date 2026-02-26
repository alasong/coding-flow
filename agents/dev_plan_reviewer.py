
from typing import Dict, Any, List, Optional
import logging
import json
from agents.base_agent import BaseAgent
from config import DEFAULT_MODEL

logger = logging.getLogger(__name__)


class DevPlanReviewerAgent(BaseAgent):
    def __init__(self, name: str = "开发计划评审专家", model_config_name: str = "dev_plan_reviewer"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=DEFAULT_MODEL)

    async def review(self, work_packages: List[Dict[str, Any]], dev_plans: List[Dict[str, Any]], requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        评审工作包和开发计划
        """
        if not getattr(self, "model", None):
            # 离线回退逻辑
            logger.info(f"[{self.name}] (离线) 执行基础评审")
            return {
                "status": "passed_with_warnings",
                "score": 80,
                "issues": [],
                "suggestions": ["离线模式无法深度评审，建议启用在线模型"],
                "summary": "基础结构完整，但缺乏深度语义分析。"
            }

        # 构造评审 Prompt
        prompt = f"""
        作为资深技术项目经理，请评审以下项目开发计划。
        
        【项目需求】
        {json.dumps(requirements, ensure_ascii=False, indent=2) if requirements else "无额外需求"}

        【工作包列表】
        {json.dumps(work_packages, ensure_ascii=False, indent=2)}
        
        【详细开发计划】
        {json.dumps(dev_plans, ensure_ascii=False, indent=2)}
        
        请重点评审：
        1. **完整性**：是否包含基础设施搭建、数据库设计、API开发、前端开发、测试及部署验收全流程？
        2. **测试覆盖**：是否每个开发任务都配套了测试任务（单元测试、集成测试）？
        3. **依赖合理性**：工作包之间的依赖关系是否清晰？
        4. **风险识别**：识别出的风险是否准确？
        
        请返回 JSON 格式的评审报告，包含：
        - status: "passed" | "passed_with_warnings" | "failed"
        - score: int (0-100)
        - issues: List[str] (发现的具体问题)
        - suggestions: List[str] (改进建议)
        - summary: str (总体评价)
        """
        
        try:
            response = await self.model([{"role": "user", "content": prompt}])
            content = await self._process_model_response(response)
            
            # 提取 JSON
            import re
            code_block_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if code_block_match:
                result = json.loads(code_block_match.group(1))
            else:
                try:
                    result = json.loads(content)
                except:
                    # 尝试非严格模式解析
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start >= 0 and end > start:
                        result = json.loads(content[start:end])
                    else:
                        raise ValueError("无法解析评审结果 JSON")
            
            logger.info(f"[{self.name}] 评审完成，得分: {result.get('score')}")
            return result
            
        except Exception as e:
            logger.error(f"[{self.name}] 评审失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "score": 0,
                "issues": ["评审过程发生异常"],
                "suggestions": ["检查模型服务状态"],
                "summary": "评审服务不可用"
            }
