import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.repo_scaffolder import RepoScaffolderAgent
from agents.api_spec_generator import APISpecGeneratorAgent
from agents.db_migration_planner import DBMigrationPlannerAgent
from agents.test_generator import TestGeneratorAgent
from agents.mock_orchestrator import MockOrchestratorAgent
from agents.ci_configurator import CIConfiguratorAgent
from agents.secure_config_agent import SecureConfigAgent
from agents.dev_run_verifier import DevRunVerifierAgent
from agents.frontend_scaffolder import FrontendScaffolderAgent
from agents.ui_mode_decider import UIModeDeciderAgent
from agents.cli_scaffolder import CLIScaffolderAgent

logger = logging.getLogger(__name__)


class DevelopmentExecutionWorkflow:
    def __init__(self,
                 scaffolder: Optional[RepoScaffolderAgent] = None,
                 api_gen: Optional[APISpecGeneratorAgent] = None,
                 db_plan: Optional[DBMigrationPlannerAgent] = None,
                 test_gen: Optional[TestGeneratorAgent] = None,
                 mocker: Optional[MockOrchestratorAgent] = None,
                 ci_conf: Optional[CIConfiguratorAgent] = None,
                 sec_conf: Optional[SecureConfigAgent] = None,
                 verifier: Optional[DevRunVerifierAgent] = None,
                 fe_scaffolder: Optional[FrontendScaffolderAgent] = None,
                 ui_decider: Optional[UIModeDeciderAgent] = None,
                 cli_scaffolder: Optional[CLIScaffolderAgent] = None):
        self.name = "项目开发工作流"
        self.scaffolder = scaffolder or RepoScaffolderAgent()
        self.api_gen = api_gen or APISpecGeneratorAgent()
        self.db_plan = db_plan or DBMigrationPlannerAgent()
        self.test_gen = test_gen or TestGeneratorAgent()
        self.mocker = mocker or MockOrchestratorAgent()
        self.ci_conf = ci_conf or CIConfiguratorAgent()
        self.sec_conf = sec_conf or SecureConfigAgent()
        self.verifier = verifier or DevRunVerifierAgent()
        self.fe_scaffolder = fe_scaffolder or FrontendScaffolderAgent()
        self.ui_decider = ui_decider or UIModeDeciderAgent()
        self.cli_scaffolder = cli_scaffolder or CLIScaffolderAgent()

    async def execute(self, decomposition_result: Dict[str, Any], requirements: Dict[str, Any] | None = None, architecture: Dict[str, Any] | None = None, output_dir: str = "output/development_execution") -> Dict[str, Any]:
        logger.info("开始执行项目开发工作流")
        result: Dict[str, Any] = {
            "workflow_name": self.name,
            "start_time": datetime.now().isoformat(),
            "status": "in_progress",
            "steps": {}
        }
        try:
            units = decomposition_result.get("final_result", {}).get("software_units", [])
            packages = decomposition_result.get("final_result", {}).get("work_packages", [])

            ui_mode = await self.ui_decider.decide(requirements, architecture)
            scaffold = await self.scaffolder.generate(units, packages, output_dir, ui_mode=ui_mode)
            result["steps"]["scaffold"] = {"status": "completed", **scaffold}
            if ui_mode == "web":
                fe = await self.fe_scaffolder.generate(units, packages, output_dir)
                result["steps"]["frontend"] = {"status": "completed", **fe}
            else:
                cli_out = await self.cli_scaffolder.generate(units, packages, output_dir)
                result["steps"]["cli"] = {"status": "completed", **cli_out}

            api_out = await self.api_gen.generate(units, packages, output_dir)
            result["steps"]["api"] = {"status": "completed", **api_out}

            db_out = await self.db_plan.plan(units, packages, output_dir)
            result["steps"]["db_migration"] = {"status": "completed", **db_out}

            mock_out = await self.mocker.prepare(units, packages, output_dir)
            result["steps"]["mock"] = {"status": "completed", **mock_out}

            tests = await self.test_gen.generate(units, packages, output_dir)
            result["steps"]["tests"] = {"status": "completed", **tests}

            ci = await self.ci_conf.configure(units, packages, output_dir)
            result["steps"]["ci"] = {"status": "completed", **ci}

            sec = await self.sec_conf.audit(output_dir)
            result["steps"]["security"] = {"status": "completed", **sec}

            verify = await self.verifier.verify(output_dir)
            result["steps"]["verify"] = {"status": "completed", **verify}

            final = {
                "scaffold": scaffold,
                "api": api_out,
                "db_migration": db_out,
                "mock": mock_out,
                "tests": tests,
                "ci": ci,
                "security": sec,
                "verify": verify
            }
            result["final_result"] = final
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
            self._save(output_dir, result)
            logger.info("项目开发工作流执行完成")
            return result
        except Exception as e:
            logger.error(f"项目开发工作流执行失败: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            self._save(output_dir, result)
            return result

    def _save(self, output_dir: str, workflow_result: Dict[str, Any]) -> None:
        import os
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        wf_file = f"{output_dir}/development_execution_result_{ts}.json"
        with open(wf_file, "w", encoding="utf-8") as f:
            json.dump(workflow_result, f, ensure_ascii=False, indent=2)
