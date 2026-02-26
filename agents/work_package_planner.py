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
        
        # 补充基础设施和测试包
        scaffold_pkg = {
            "id": "WP-INFRA-001",
            "name": "项目基础设施初始化",
            "objective": "搭建项目基础环境，配置CI/CD及公共模块",
            "acceptance_criteria": ["环境启动成功", "流水线跑通", "公共模块可用"],
            "software_unit_ids": ["INFRA::Scaffold", "INFRA::CI/CD", "INFRA::CommonLib"],
            "subtask_ids": [],
            "assignees": [],
            "status": "planned",
            "priority": "high",
            "parallelizable": False,
            "tags": ["infrastructure", "scaffold"]
        }
        
        test_pkg = {
            "id": "WP-TEST-001",
            "name": "系统集成与验收测试",
            "objective": "执行端到端测试，验证系统整体功能",
            "acceptance_criteria": ["E2E测试通过", "性能指标达标", "安全扫描通过"],
            "software_unit_ids": ["TEST::IntegrationSuites", "TEST::E2E", "TEST::SecurityScan"],
            "subtask_ids": [],
            "assignees": [],
            "status": "planned",
            "priority": "low", # 通常在最后执行
            "parallelizable": False,
            "tags": ["testing", "qa"]
        }
        
        # 基础设施包放最前，测试包放最后
        packages.insert(0, scaffold_pkg)
        packages.append(test_pkg)
        
        # 补充交付验收包
        delivery_pkg = {
            "id": "WP-DELIVERY-001",
            "name": "项目交付与验收",
            "objective": "完成用户验收测试(UAT)及文档移交",
            "acceptance_criteria": ["UAT签字确认", "所有文档归档", "生产环境部署就绪"],
            "software_unit_ids": ["DELIVERY::UAT", "DELIVERY::Docs", "DELIVERY::Release"],
            "subtask_ids": [],
            "assignees": [],
            "status": "planned",
            "priority": "low",
            "parallelizable": False,
            "tags": ["delivery", "acceptance"]
        }
        packages.append(delivery_pkg)
        
        return packages

