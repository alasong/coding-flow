from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DevPlanGeneratorAgent:
    def __init__(self, name: str = "开发计划生成专家"):
        self.name = name

    async def generate(self, work_packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                }
            }
            plans.append(plan)
        logger.info(f"[{self.name}] 生成开发计划 {len(plans)} 项")
        return plans

