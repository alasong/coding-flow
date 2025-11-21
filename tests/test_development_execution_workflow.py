import asyncio
import os
from workflow.development_workflow import ProjectDevelopmentWorkflow
from workflow.development_execution_workflow import DevelopmentExecutionWorkflow


def make_arch():
    return {
        "system_architecture": {"system_components": [{"name": "User Service"}]},
        "database_design": {"database_type": "MySQL", "tables": [{"name": "users"}]},
        "api_architecture": {"api_style": "REST", "api_endpoints": [{"path": "/api/v1/users", "method": "GET"}]}
    }


def test_dev_execution(tmp_path):
    output_dir = str(tmp_path)
    async def run():
        decomp = ProjectDevelopmentWorkflow()
        decomp_result = await decomp.execute(make_arch(), output_dir=output_dir)
        devexec = DevelopmentExecutionWorkflow()
        res = await devexec.execute(decomp_result, output_dir=os.path.join(output_dir, "development_execution"))
        return res

    result = asyncio.get_event_loop().run_until_complete(run())
    assert result["status"] == "completed"
    files = os.listdir(os.path.join(output_dir, "development_execution"))
    assert any(f.startswith("development_execution_result_") for f in files)

