import asyncio
import os
from workflow.development_workflow import ProjectDevelopmentWorkflow
from workflow.development_execution_workflow import DevelopmentExecutionWorkflow
from workflow.deployment_workflow import DeploymentWorkflow


def make_arch():
    return {
        "system_architecture": {"system_components": [{"name": "User Service"}], "technology_stack": {"frontend": "HTML"}},
        "database_design": {"database_type": "PostgreSQL", "tables": [{"name": "users"}]},
        "api_architecture": {"api_style": "REST", "api_endpoints": [{"path": "/api/v1/users", "method": "GET"}]}
    }


def test_deployment(tmp_path):
    out = str(tmp_path)
    async def run():
        decomp = ProjectDevelopmentWorkflow()
        dres = await decomp.execute(make_arch(), output_dir=os.path.join(out, "decomposition"))
        dev = DevelopmentExecutionWorkflow()
        exres = await dev.execute(dres, output_dir=os.path.join(out, "development_execution"))
        dep = DeploymentWorkflow()
        return await dep.execute(exres, output_dir=os.path.join(out, "deployment"))

    res = asyncio.get_event_loop().run_until_complete(run())
    assert res["status"] == "completed"
    dep_dir = os.path.join(out, "deployment")
    assert os.path.exists(os.path.join(dep_dir, "docker", "Dockerfile"))
    assert os.path.exists(os.path.join(dep_dir, "docker", "docker-compose.yml"))
    assert os.path.exists(os.path.join(dep_dir, "env", "dev.env"))

