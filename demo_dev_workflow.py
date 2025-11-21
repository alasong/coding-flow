import asyncio
from workflow.development_workflow import ProjectDevelopmentWorkflow


def make_architecture_analysis():
    return {
        "system_architecture": {
            "architecture_pattern": "微服务",
            "system_components": [
                {"name": "User Service", "description": "用户相关服务"},
                {"name": "Order Service", "description": "订单处理"}
            ]
        },
        "database_design": {
            "database_type": "MySQL",
            "tables": [
                {"name": "users", "description": "用户表"},
                {"name": "orders", "description": "订单表"}
            ]
        },
        "api_architecture": {
            "api_style": "REST",
            "api_endpoints": [
                {"path": "/api/v1/users", "method": "GET", "description": "获取用户"},
                {"path": "/api/v1/orders", "method": "POST", "description": "创建订单"}
            ]
        }
    }


async def main():
    wf = ProjectDevelopmentWorkflow()
    result = await wf.execute(make_architecture_analysis(), output_dir="output")
    print("status:", result["status"])
    print("coverage:", result["steps"]["coverage"]["coverage_percentage"])
    print("batches:", len(result["steps"]["concurrency"]["batches"]))


if __name__ == "__main__":
    asyncio.run(main())

