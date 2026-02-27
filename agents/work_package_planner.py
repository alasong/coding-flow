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
            chunk_size = max(1, self.max_units_per_package)
            for i in range(0, len(units_sorted), chunk_size):
                chunk = units_sorted[i:i + chunk_size]
                if len(chunk) > 1:
                    for u in chunk:
                        packages.append(self._build_unit_package(u, key, pkg_id_counter))
                        pkg_id_counter += 1
                else:
                    u = chunk[0]
                    packages.append(self._build_unit_package(u, key, pkg_id_counter))
                    pkg_id_counter += 1

        base_count = len(packages)
        logger.info(f"[{self.name}] 规划生成工作包 {base_count} 个(单元包)")

        infra_packages = self._build_infra_packages()
        quality_packages = self._build_quality_packages(packages)
        test_packages = self._build_test_packages()
        delivery_packages = self._build_delivery_packages()

        packages = infra_packages + packages + quality_packages + test_packages + delivery_packages
        logger.info(f"[{self.name}] 工作包总数 {len(packages)} 个(含基础设施/质量收敛/测试/交付)")
        packages = self._assign_dependencies(packages, software_units)

        return packages

    def _build_unit_package(self, unit: Dict[str, Any], key: str, pkg_id_counter: int) -> Dict[str, Any]:
        return {
            "id": f"WP-{pkg_id_counter:03d}",
            "name": f"{key}::{unit.get('name')}",
            "objective": f"实现 {unit.get('name')} 单元",
            "acceptance_criteria": ["功能达成", "测试通过", "无阻断风险"],
            "software_unit_ids": [unit["id"]],
            "subtask_ids": [],
            "assignees": [],
            "status": "planned",
            "priority": "high" if unit.get("risk_level") == "high" else "medium",
            "parallelizable": True,
            "tags": [unit.get("type")]
        }


    def _build_infra_packages(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "WP-INFRA-001",
                "name": "infrastructure/scaffold::RepoSetup",
                "objective": "初始化仓库结构与基础配置",
                "acceptance_criteria": ["代码仓库可用", "基础目录结构就绪"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "high",
                "parallelizable": False,
                "tags": ["infrastructure", "scaffold"]
            },
            {
                "id": "WP-INFRA-002",
                "name": "infrastructure/ci::PipelineSetup",
                "objective": "配置 CI/CD 基础流水线",
                "acceptance_criteria": ["流水线跑通", "基础构建通过"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "high",
                "parallelizable": False,
                "tags": ["infrastructure", "ci"]
            },
            {
                "id": "WP-INFRA-003",
                "name": "infrastructure/common::CommonLib",
                "objective": "建立公共模块基础设施",
                "acceptance_criteria": ["公共模块可复用", "异常与日志可用"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "high",
                "parallelizable": False,
                "tags": ["infrastructure", "common"]
            }
        ]

    def _build_quality_packages(self, unit_packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def collect_ids(tag: str) -> List[str]:
            return [p["id"] for p in unit_packages if tag in p.get("tags", [])]

        quality_defs = [
            ("WP-QUALITY-001", "quality/db::Convergence", "数据库质量收敛", "db"),
            ("WP-QUALITY-002", "quality/component::Convergence", "组件质量收敛", "component"),
            ("WP-QUALITY-003", "quality/api::Convergence", "接口质量收敛", "api"),
            ("WP-QUALITY-004", "quality/frontend::Convergence", "前端质量收敛", "frontend")
        ]

        packages: List[Dict[str, Any]] = []
        for pkg_id, name, objective, scope in quality_defs:
            depends_on = collect_ids(scope)
            if not depends_on:
                continue
            packages.append({
                "id": pkg_id,
                "name": name,
                "objective": objective,
                "acceptance_criteria": ["质量标准达成", "风险收敛完成"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "high",
                "parallelizable": False,
                "tags": ["quality"],
                "quality_scope": scope,
                "depends_on": depends_on
            })
        return packages

    def _build_test_packages(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "WP-TEST-001",
                "name": "testing/integration::Suites",
                "objective": "编写集成测试套件",
                "acceptance_criteria": ["集成测试通过"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "low",
                "parallelizable": False,
                "tags": ["testing", "qa"]
            },
            {
                "id": "WP-TEST-002",
                "name": "testing/e2e::Scenarios",
                "objective": "编写端到端测试脚本",
                "acceptance_criteria": ["E2E测试通过"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "low",
                "parallelizable": False,
                "tags": ["testing", "qa"]
            },
            {
                "id": "WP-TEST-003",
                "name": "testing/perf::Benchmarks",
                "objective": "执行性能测试",
                "acceptance_criteria": ["性能指标达标"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "low",
                "parallelizable": False,
                "tags": ["testing", "qa"]
            },
            {
                "id": "WP-TEST-004",
                "name": "testing/security::Scan",
                "objective": "执行安全扫描",
                "acceptance_criteria": ["安全扫描通过"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "low",
                "parallelizable": False,
                "tags": ["testing", "qa"]
            }
        ]

    def _build_delivery_packages(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "WP-DELIVERY-001",
                "name": "delivery/uat::Support",
                "objective": "支持用户验收测试(UAT)",
                "acceptance_criteria": ["UAT签字确认"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "low",
                "parallelizable": False,
                "tags": ["delivery", "acceptance"]
            },
            {
                "id": "WP-DELIVERY-002",
                "name": "delivery/docs::Handover",
                "objective": "完成文档移交与归档",
                "acceptance_criteria": ["所有文档归档"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "low",
                "parallelizable": False,
                "tags": ["delivery", "acceptance"]
            },
            {
                "id": "WP-DELIVERY-003",
                "name": "delivery/release::Ready",
                "objective": "准备生产环境发布",
                "acceptance_criteria": ["生产环境部署就绪"],
                "software_unit_ids": [],
                "subtask_ids": [],
                "assignees": [],
                "status": "planned",
                "priority": "low",
                "parallelizable": False,
                "tags": ["delivery", "acceptance"]
            }
        ]

    def _assign_dependencies(self, packages: List[Dict[str, Any]], software_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unit_index = {u["id"]: u for u in software_units}
        unit_to_pkg = {}
        for p in packages:
            for uid in p.get("software_unit_ids", []):
                unit_to_pkg[uid] = p["id"]

        stage_map: Dict[int, List[str]] = {}
        for p in packages:
            stage = self._stage_for_pkg(p)
            stage_map.setdefault(stage, []).append(p["id"])

        for p in packages:
            deps = set(p.get("depends_on", []))
            stage = self._stage_for_pkg(p)
            tags = set(p.get("tags", []))
            if "quality" in tags:
                pass
            elif stage == 6:
                deps.update(stage_map.get(5, []))
                if not stage_map.get(5):
                    deps.update(stage_map.get(4, []))
            elif stage == 7:
                deps.update(stage_map.get(6, []))
            elif stage > 0:
                deps.update(stage_map.get(stage - 1, []))

            for uid in p.get("software_unit_ids", []):
                unit = unit_index.get(uid, {})
                for dep_uid in unit.get("dependencies", []):
                    dep_pkg = unit_to_pkg.get(dep_uid)
                    if dep_pkg:
                        deps.add(dep_pkg)

            p["depends_on"] = sorted(deps)
        return packages

    def _stage_for_pkg(self, pkg: Dict[str, Any]) -> int:
        tags = set(pkg.get("tags", []))
        if "infrastructure" in tags:
            return 0
        if "db" in tags:
            return 1
        if "component" in tags:
            return 2
        if "api" in tags:
            return 3
        if "frontend" in tags:
            return 4
        if "quality" in tags:
            return 5
        if "testing" in tags:
            return 6
        if "delivery" in tags or "acceptance" in tags:
            return 7
        return 3

