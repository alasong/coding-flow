import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.repo_scaffolder import RepoScaffolderAgent
from agents.api_spec_generator import APISpecGeneratorAgent
from agents.db_migration_planner import DBMigrationPlannerAgent
from agents.code_generator import CodeGeneratorAgent
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
                 code_gen: Optional[CodeGeneratorAgent] = None,
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
        self.code_gen = code_gen or CodeGeneratorAgent()
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

            # --- Git 初始化与分支管理 ---
            # 1. 确保脚手架生成了 Git 仓库
            ui_mode = await self.ui_decider.decide(requirements, architecture)
            scaffold = await self.scaffolder.generate(units, packages, output_dir, ui_mode=ui_mode)
            result["steps"]["scaffold"] = {"status": "completed", **scaffold}
            
            # 2. 自动提交脚手架代码
            await self._git_commit(output_dir, "Initial commit: Project scaffold")
            
            # 3. 创建开发分支 (假设所有任务在一个 dev 分支上，或者为每个工作包创建分支)
            # 这里简单起见，创建一个 dev 分支
            await self._git_checkout_new_branch(output_dir, "develop")
            # ---------------------------

            if ui_mode == "web":
                fe = await self.fe_scaffolder.generate(units, packages, output_dir)
                result["steps"]["frontend"] = {"status": "completed", **fe}
            else:
                cli_out = await self.cli_scaffolder.generate(units, packages, output_dir)
                result["steps"]["cli"] = {"status": "completed", **cli_out}
            
            # 提交前端/CLI代码
            await self._git_commit(output_dir, "Feat: Frontend/CLI scaffold")
            
            # 生成业务代码存根
            code_out = await self.code_gen.generate(units, packages, output_dir)
            result["steps"]["code_gen"] = {"status": "completed", **code_out}
            
            # 提交业务代码
            await self._git_commit(output_dir, "Feat: Business logic implementation")

            api_out = await self.api_gen.generate(units, packages, output_dir)
            result["steps"]["api"] = {"status": "completed", **api_out}
            
            # 提交 API 代码
            await self._git_commit(output_dir, "Feat: API implementation")

            db_out = await self.db_plan.plan(units, packages, output_dir)
            result["steps"]["db_migration"] = {"status": "completed", **db_out}
            
            mock_out = await self.mocker.prepare(units, packages, output_dir)
            result["steps"]["mock"] = {"status": "completed", **mock_out}
            
            tests = await self.test_gen.generate(units, packages, output_dir)
            result["steps"]["tests"] = {"status": "completed", **tests}
            
            # 提交测试代码
            await self._git_commit(output_dir, "Test: Unit and integration tests")
            
            # 立即执行测试验证
            verify = await self.verifier.verify(output_dir)
            
            # 自动修复循环 (Auto-Repair Loop)
            max_retries = 3
            retry_count = 0
            
            while not verify.get("tests") and retry_count < max_retries:
                retry_count += 1
                logger.warning(f"测试验证失败，尝试自动修复 ({retry_count}/{max_retries})...")
                
                # 提取错误日志
                error_log = verify.get("output", "")
                
                if hasattr(self.code_gen, "repair"):
                     await self.code_gen.repair(output_dir, error_log)
                     # 提交修复后的代码
                     await self._git_commit(output_dir, f"Fix: Auto-repair attempt {retry_count}")
                     
                     # 重新运行测试
                     verify = await self.verifier.verify(output_dir)
                else:
                     logger.warning("CodeGeneratorAgent 不支持自动修复，跳过重试")
                     break
            
            result["steps"]["verify"] = {"status": "completed", **verify}
            
            # 如果测试失败，尝试修复（可选）
            if not verify.get("tests"):
                logger.warning("测试执行失败，建议检查 verify_report.md")
            else:
                # 测试通过，合并回主分支 (模拟)
                # await self._git_merge(output_dir, "develop", "main")
                pass

            ci = await self.ci_conf.configure(units, packages, output_dir)
            result["steps"]["ci"] = {"status": "completed", **ci}
            
            sec = await self.sec_conf.audit(output_dir)
            result["steps"]["security"] = {"status": "completed", **sec}

            final = {
                "scaffold": scaffold,
                "api": api_out,
                "db_migration": db_out,
                "mock": mock_out,
                "tests": tests,
                "verify": verify,
                "ci": ci,
                "security": sec
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

    async def _git_commit(self, output_dir: str, message: str) -> None:
        """Helper to commit changes to git"""
        import os
        import subprocess
        base = os.path.join(output_dir, "project_code")
        if not os.path.exists(os.path.join(base, ".git")):
             return # Not a git repo
        
        try:
            # Check if there are changes
            status = subprocess.run(["git", "status", "--porcelain"], cwd=base, capture_output=True, text=True)
            if not status.stdout.strip():
                return # No changes
                
            subprocess.run(["git", "add", "."], cwd=base, check=True)
            subprocess.run(["git", "commit", "-m", message], cwd=base, check=True)
            logger.info(f"Git commit: {message}")
        except Exception as e:
            logger.warning(f"Git commit failed: {e}")

    async def _git_checkout_new_branch(self, output_dir: str, branch_name: str) -> None:
        """Helper to create and switch to a new branch"""
        import os
        import subprocess
        base = os.path.join(output_dir, "project_code")
        if not os.path.exists(os.path.join(base, ".git")):
             return
             
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=base, check=True)
            logger.info(f"Switched to new branch: {branch_name}")
        except Exception as e:
             # Try checking out if already exists
             try:
                 subprocess.run(["git", "checkout", branch_name], cwd=base, check=True)
             except:
                 logger.warning(f"Git checkout failed: {e}")
