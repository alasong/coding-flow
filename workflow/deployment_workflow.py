import json
import os
from datetime import datetime
import subprocess
from typing import Dict, Any, Optional

from agents.dockerfile_generator import DockerfileGeneratorAgent
from agents.compose_generator import ComposeGeneratorAgent
from agents.helm_chart_generator import HelmChartGeneratorAgent
from agents.env_config_agent import EnvConfigAgent
from agents.migration_runner import MigrationRunnerAgent
from agents.readiness_prober import ReadinessProberAgent
from agents.observability_configurator import ObservabilityConfiguratorAgent
from agents.cd_configurator import CDConfiguratorAgent
from agents.security_scanner import SecurityScannerAgent
from agents.preflight_generator import PreflightGeneratorAgent


class DeploymentWorkflow:
    def __init__(self,
                 dockerfile: Optional[DockerfileGeneratorAgent] = None,
                 compose: Optional[ComposeGeneratorAgent] = None,
                 helm: Optional[HelmChartGeneratorAgent] = None,
                 envcfg: Optional[EnvConfigAgent] = None,
                 migration: Optional[MigrationRunnerAgent] = None,
                 prober: Optional[ReadinessProberAgent] = None,
                 observ: Optional[ObservabilityConfiguratorAgent] = None,
                 cdconf: Optional[CDConfiguratorAgent] = None,
                 secscan: Optional[SecurityScannerAgent] = None,
                 preflight: Optional[PreflightGeneratorAgent] = None):
        self.name = "项目部署工作流"
        self.dockerfile = dockerfile or DockerfileGeneratorAgent()
        self.compose = compose or ComposeGeneratorAgent()
        self.helm = helm or HelmChartGeneratorAgent()
        self.envcfg = envcfg or EnvConfigAgent()
        self.migration = migration or MigrationRunnerAgent()
        self.prober = prober or ReadinessProberAgent()
        self.observ = observ or ObservabilityConfiguratorAgent()
        self.cdconf = cdconf or CDConfiguratorAgent()
        self.secscan = secscan or SecurityScannerAgent()
        self.preflight = preflight or PreflightGeneratorAgent()

    async def execute(self, development_result: Dict[str, Any], requirements: Optional[Dict[str, Any]] = None, architecture: Optional[Dict[str, Any]] = None, output_dir: str = "output/deployment") -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "workflow_name": self.name,
            "start_time": datetime.now().isoformat(),
            "status": "in_progress",
            "steps": {}
        }
        os.makedirs(output_dir, exist_ok=True)
        final_dev = development_result.get("final_result", {})
        scaffold = final_dev.get("scaffold", {})
        code_dir = scaffold.get("code_dir")
        ui_mode = "web" if development_result.get("steps", {}).get("frontend") else "cli"

        mode = "compose"
        await self.dockerfile.generate(code_dir, output_dir, ui_mode)
        result["steps"]["dockerfile"] = {"status": "completed"}
        await self.envcfg.generate(output_dir)
        result["steps"]["env"] = {"status": "completed"}
        await self.migration.generate(output_dir)
        result["steps"]["migration"] = {"status": "completed"}
        await self.prober.generate(output_dir)
        result["steps"]["prober"] = {"status": "completed"}
        await self.observ.generate(output_dir)
        result["steps"]["observability"] = {"status": "completed"}
        if mode == "compose":
            rel = os.path.relpath(code_dir, output_dir) if code_dir else ""
            await self.compose.generate(output_dir, rel)
            result["steps"]["compose"] = {"status": "completed"}
        else:
            await self.helm.generate(output_dir)
            result["steps"]["helm"] = {"status": "completed"}
        rel_code = os.path.relpath(code_dir, output_dir) if code_dir else "project_code"
        pre = await self.preflight.generate(output_dir, rel_code)
        result["steps"]["preflight"] = {"status": "completed", **pre}
        await self.cdconf.generate(output_dir, mode)
        result["steps"]["cd"] = {"status": "completed"}
        await self.secscan.generate(output_dir)
        result["steps"]["security_scan"] = {"status": "completed"}

        compose_started = False
        try:
            from config import DEPLOYMENT_WORKFLOW_CONFIG
            if mode == "compose" and DEPLOYMENT_WORKFLOW_CONFIG.get("auto_start_compose", False):
                docker_dir = os.path.join(output_dir, "docker")
                if os.path.exists(os.path.join(docker_dir, "docker-compose.yml")):
                    cmd = "docker compose up -d"
                    try:
                        subprocess.run(cmd, cwd=docker_dir, shell=True, check=True)
                        compose_started = True
                    except Exception:
                        cmd2 = "docker-compose up -d"
                        subprocess.run(cmd2, cwd=docker_dir, shell=True, check=False)
                        compose_started = True
        except Exception:
            compose_started = False

        result["final_result"] = {
            "mode": mode,
            "output_dir": output_dir,
            "env": {
                "health_url": "http://localhost:8000/health",
                "ui_url": "http://localhost:8000/ui/",
                "compose_started": compose_started
            }
        }
        result["status"] = "completed"
        result["end_time"] = datetime.now().isoformat()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(output_dir, f"deployment_result_{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result
