import asyncio
import os
from workflow.development_workflow import ProjectDevelopmentWorkflow
from workflow.development_execution_workflow import DevelopmentExecutionWorkflow
from workflow.deployment_workflow import DeploymentWorkflow


async def main():
    project_dir = "output/demo-project"
    arch = {
        "system_architecture": {"system_components": [{"name": "User Service"}], "technology_stack": {"frontend": "HTML"}},
        "database_design": {"database_type": "PostgreSQL", "tables": [{"name": "users"}]},
        "api_architecture": {"api_style": "REST", "api_endpoints": [{"path": "/api/v1/users", "method": "GET"}]}
    }
    decomp = ProjectDevelopmentWorkflow()
    dres = await decomp.execute(arch, output_dir=os.path.join(project_dir, "decomposition"))
    devexec = DevelopmentExecutionWorkflow()
    exres = await devexec.execute(dres, output_dir=os.path.join(project_dir, "development_execution"))
    deploy = DeploymentWorkflow()
    dep = await deploy.execute(exres, output_dir=os.path.join(project_dir, "deployment"))
    print("deployment:", dep.get("status"), dep.get("final_result", {}).get("output_dir"))


if __name__ == "__main__":
    asyncio.run(main())

