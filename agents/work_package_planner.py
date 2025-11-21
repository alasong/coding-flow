from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WorkPackagePlannerAgent:
    def __init__(self, name: str = "工作包规划专家", max_units_per_package: int = 3):
        self.name = name
        self.max_units_per_package = max_units_per_package

    async def plan(self, software_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for u in software_units:
            key = f"{u.get('context','')}/{u.get('type','')}"
            buckets.setdefault(key, []).append(u)

        packages: List[Dict[str, Any]] = []
        pkg_id_counter = 1
        for key, units in buckets.items():
            units_sorted = sorted(units, key=lambda x: x.get("risk_level", "low"), reverse=True)
            for i in range(0, len(units_sorted), self.max_units_per_package):
                chunk = units_sorted[i:i + self.max_units_per_package]
                pkg = {
                    "id": f"WP-{pkg_id_counter:03d}",
                    "name": f"{key}#{i//self.max_units_per_package+1}",
                    "objective": f"实现 {key} 下 {len(chunk)} 个单元",
                    "acceptance_criteria": ["功能达成", "测试通过", "无阻断风险"],
                    "software_unit_ids": [c["id"] for c in chunk],
                    "subtask_ids": [],
                    "assignees": [],
                    "status": "planned",
                    "priority": "medium",
                    "parallelizable": True,
                    "tags": [u.get("type") for u in chunk]
                }
                packages.append(pkg)
                pkg_id_counter += 1

        logger.info(f"[{self.name}] 规划生成工作包 {len(packages)} 个")
        return packages

