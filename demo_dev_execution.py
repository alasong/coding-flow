import asyncio
from workflow.development_execution_workflow import DevelopmentExecutionWorkflow
from workflow.development_workflow import ProjectDevelopmentWorkflow


async def main():
    decomp = ProjectDevelopmentWorkflow()
    arch = {
        "system_architecture": {"system_components": [{"name": "User Service"}]},
        "database_design": {"database_type": "MySQL", "tables": [{"name": "users"}]},
        "api_architecture": {"api_style": "REST", "api_endpoints": [{"path": "/api/v1/users", "method": "GET"}]}
    }
    decomp_result = await decomp.execute(arch)
    devexec = DevelopmentExecutionWorkflow()
    result = await devexec.execute(decomp_result)
    print("status:", result.get("status"))


if __name__ == "__main__":
    asyncio.run(main())

