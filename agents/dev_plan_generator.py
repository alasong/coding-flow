from typing import List, Dict, Any
import logging
import json
from agents.base_agent import BaseAgent

from config import DEV_MODEL

logger = logging.getLogger(__name__)


class DevPlanGeneratorAgent(BaseAgent):
    def __init__(self, name: str = "开发计划生成专家", model_config_name: str = "dev_plan_generator"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=DEV_MODEL)

    async def generate(self, work_packages: List[Dict[str, Any]], requirements: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if not getattr(self, "model", None):
             # 离线回退逻辑
            print("DEBUG: Using offline logic")
            plans: List[Dict[str, Any]] = []
            for p in work_packages:
                plan = {
                    "package_id": p["id"],
                    "status_machine": ["planned", "in_progress", "review", "testing", "done"],
                    "acceptance_criteria": p.get("acceptance_criteria", ["功能达成", "测试通过", "无阻断风险"]),
                    "risk": "low",
                    "dependencies": [],
                    "estimate": {
                        "points": max(1, len(p.get("software_unit_ids", [])))
                    },
                    "tasks": [f"实现 {uid}" for uid in p.get("software_unit_ids", [])] + 
                             [f"编写 {uid} 的单元测试" for uid in p.get("software_unit_ids", [])] +
                             ["编写集成测试脚本"]
                }
                plans.append(plan)
            logger.info(f"[{self.name}] (离线) 生成开发计划 {len(plans)} 项")
            return plans

        # 使用 LLM 生成更详细的计划
        prompt = f"""
        作为开发计划生成专家，请根据以下工作包列表，生成详细的开发计划。
        
        【项目需求】
        {json.dumps(requirements, ensure_ascii=False, indent=2) if requirements else "无额外需求"}

        【工作包列表】
        {json.dumps(work_packages, ensure_ascii=False, indent=2)}
        
        请为每个工作包生成以下信息，并根据 **tags** 类型智能调整任务内容：
        
        1. **基础设施包 (tags: infrastructure)**:
           - 必须包含 Dockerfile/docker-compose 编写。
           - 必须包含 CI/CD 流水线配置。
           - 必须包含公共库 (Logger, ErrorHandler) 开发。
           
        2. **数据库包 (tags: db)**:
           - 必须包含 Schema 设计与 SQL 编写。
           - 必须包含 Migration 脚本开发。
           - **不要生成单元测试任务**，改为“数据迁移测试”。
           
        3. **API/后端包 (tags: api/component)**:
           - 必须包含接口编码。
           - 必须包含单元测试开发 (Unit Tests)。
           - 必须包含 API 文档编写 (Swagger/OpenAPI)。
           - **不要生成集成测试脚本开发** (已由专用测试包负责)。
           
        4. **前端包 (tags: frontend)**:
           - 必须包含组件编码。
           - 必须包含 UI/交互测试。
           
        5. **测试包 (tags: testing)**:
           - 必须包含编写集成测试套件。
           - 必须包含编写 E2E 测试脚本。
           - 必须包含性能测试与安全扫描。
           
        6. **交付/验收包 (tags: delivery/acceptance)**:
           - 必须包含 Staging 环境部署。
           - 必须包含用户验收测试 (UAT) 支持。
           - 必须包含用户手册与运维文档移交。
           - 必须包含项目验收报告编写。
        
        请返回 JSON 格式的列表，每个元素包含：
        - package_id: 对应的工作包ID
        - tasks: [str] 任务列表
        - estimate_points: int 预估点数
        - risk_level: str 风险等级
        - risk_reason: str 风险原因
        - acceptance_criteria: [str] 验收标准 (需包含测试覆盖率或通过率)
        """
        
        try:
            response = await self.model([{"role": "user", "content": prompt}])
            content = await self._process_model_response(response)
            
            # 使用基类的 JSON 提取能力
            if hasattr(self, '_extract_json'):
                plans = self._extract_json(content, expected_type=list)
            else:
                import re
                code_block_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if code_block_match:
                    plans = json.loads(code_block_match.group(1))
                else:
                    plans = json.loads(content)
            
            if not plans:
                raise ValueError("生成的计划为空或解析失败")

            logger.info(f"[{self.name}] 生成开发计划 {len(plans)} 项")
            return plans
            
        except Exception as e:
            logger.error(f"[{self.name}] 开发计划生成失败: {e}")
            # 失败回退
            return await self.generate_offline(work_packages)

    def _extract_json(self, content: str, expected_type=dict):
        """提取并解析JSON (增强版)"""
        import re
        try:
            # 移除 Markdown 代码块标记
            code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if code_block_match:
                content = code_block_match.group(1)
            
            # 尝试解析
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] JSON解析失败")
            return None



    async def generate_offline(self, work_packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        plans: List[Dict[str, Any]] = []
        for p in work_packages:
            tags = p.get("tags", [])
            tasks = []
            
            # 根据类型生成任务
            if "infrastructure" in tags:
                tasks = ["编写 Dockerfile", "配置 CI/CD 流水线", "开发公共日志库", "开发异常处理模块"]
            elif "testing" in tags:
                tasks = ["编写集成测试套件", "编写 E2E 测试脚本", "执行性能测试", "执行安全扫描"]
            elif "delivery" in tags or "acceptance" in tags:
                tasks = ["部署 Staging 环境", "支持用户验收测试(UAT)", "移交用户手册", "编写项目验收报告"]
            elif "db" in tags:
                tasks = [f"设计 {uid} 表结构" for uid in p.get("software_unit_ids", [])] + \
                        ["编写 Migration 脚本", "执行数据迁移测试"]
            elif "frontend" in tags:
                tasks = [f"实现 {uid} 组件" for uid in p.get("software_unit_ids", [])] + \
                        [f"编写 {uid} UI 测试" for uid in p.get("software_unit_ids", [])]
            else: # api, component, default
                tasks = [f"实现 {uid}" for uid in p.get("software_unit_ids", [])] + \
                        [f"编写 {uid} 的单元测试" for uid in p.get("software_unit_ids", [])] + \
                        ["编写 API 文档"]

            plan = {
                "package_id": p["id"],
                "status_machine": ["planned", "in_progress", "review", "testing", "done"],
                "acceptance_criteria": p.get("acceptance_criteria", ["功能达成", "测试通过", "无阻断风险"]),
                "risk": "low",
                "dependencies": [],
                "estimate": {
                    "points": max(1, len(p.get("software_unit_ids", [])))
                },
                "tasks": tasks
            }
            plans.append(plan)
        return plans

