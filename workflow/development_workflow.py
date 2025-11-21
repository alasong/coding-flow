import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.software_unit_extractor import SoftwareUnitExtractorAgent
from agents.work_package_planner import WorkPackagePlannerAgent
from agents.unit_workpackage_matcher import UnitToWorkPackageMatcherAgent
from agents.coverage_auditor import CoverageAuditorAgent
from agents.concurrency_orchestrator import ConcurrencyOrchestratorAgent
from agents.dev_plan_generator import DevPlanGeneratorAgent
from agents.dev_document_exporter import DevDocumentExporterAgent

logger = logging.getLogger(__name__)


class ProjectDevelopmentWorkflow:
    def __init__(self,
                 extractor: Optional[SoftwareUnitExtractorAgent] = None,
                 planner: Optional[WorkPackagePlannerAgent] = None,
                 matcher: Optional[UnitToWorkPackageMatcherAgent] = None,
                 auditor: Optional[CoverageAuditorAgent] = None,
                 orchestrator: Optional[ConcurrencyOrchestratorAgent] = None,
                 plan_generator: Optional[DevPlanGeneratorAgent] = None,
                 exporter: Optional[DevDocumentExporterAgent] = None):

        self.name = "项目分解工作流"
        self.extractor = extractor or SoftwareUnitExtractorAgent()
        self.planner = planner or WorkPackagePlannerAgent()
        self.matcher = matcher or UnitToWorkPackageMatcherAgent()
        self.auditor = auditor or CoverageAuditorAgent()
        self.orchestrator = orchestrator or ConcurrencyOrchestratorAgent()
        self.plan_generator = plan_generator or DevPlanGeneratorAgent()
        self.exporter = exporter or DevDocumentExporterAgent()

    async def execute(self, architecture_analysis: Dict[str, Any], output_dir: str = "output") -> Dict[str, Any]:
        logger.info("开始执行项目分解工作流")
        result: Dict[str, Any] = {
            "workflow_name": self.name,
            "start_time": datetime.now().isoformat(),
            "status": "in_progress",
            "steps": {}
        }

        try:
            units = await self.extractor.extract(architecture_analysis)
            result["steps"]["software_units"] = {"status": "completed", "count": len(units)}

            packages = await self.planner.plan(units)
            match_out = await self.matcher.match(units, packages)
            packages = match_out["work_packages"]
            result["steps"]["work_packages"] = {"status": "completed", "count": len(packages)}
            result["steps"]["matching"] = {"status": "completed", "unbound": match_out["unbound_units"], "wrong": match_out["wrong_bindings"]}

            coverage = await self.auditor.audit(units, packages)
            # 覆盖门禁：若未覆盖则创建补救包
            if coverage.get("uncovered_units"):
                remedial_pkg = {
                    "id": f"WP-FIX-{datetime.now().strftime('%H%M%S')}",
                    "name": "remedial",
                    "objective": "补充未覆盖单元",
                    "acceptance_criteria": ["所有单元挂载完成"],
                    "software_unit_ids": coverage["uncovered_units"],
                    "subtask_ids": [],
                    "assignees": [],
                    "status": "planned",
                    "priority": "high",
                    "parallelizable": True,
                    "tags": ["remedial"]
                }
                packages.append(remedial_pkg)
                coverage = await self.auditor.audit(units, packages)

            if coverage.get("coverage_percentage", 0) < 100:
                raise Exception("覆盖度未达到100%，门禁阻断")

            result["steps"]["coverage"] = {"status": "completed", **coverage}

            concurrency = await self.orchestrator.plan_batches(packages, units)
            result["steps"]["concurrency"] = {"status": "completed", **concurrency}

            dev_plans = await self.plan_generator.generate(packages)
            result["steps"]["dev_plan"] = {"status": "completed", "count": len(dev_plans)}

            docs = await self.exporter.export(units, packages, coverage, concurrency, dev_plans)

            final = {
                "software_units": units,
                "work_packages": packages,
                "coverage_report": coverage,
                "concurrency_plan": concurrency,
                "dev_plans": dev_plans,
                "documents": docs
            }
            result["final_result"] = final
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()

            self._save(output_dir, result)
            logger.info("项目分解工作流执行完成")
            return result

        except Exception as e:
            logger.error(f"项目分解工作流执行失败: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            self._save(output_dir, result)
            return result

    def _save(self, output_dir: str, workflow_result: Dict[str, Any]) -> None:
        import os
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        wf_file = f"{output_dir}/development_workflow_result_{ts}.json"
        with open(wf_file, "w", encoding="utf-8") as f:
            json.dump(workflow_result, f, ensure_ascii=False, indent=2)
        docs = workflow_result.get("final_result", {}).get("documents", {})
        if docs.get("development_overview_md"):
            md_file = f"{output_dir}/development_overview_{ts}.md"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(docs["development_overview_md"])
