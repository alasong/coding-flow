import asyncio
import os
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


def test_development_workflow_runs(tmp_path):
    output_dir = str(tmp_path)
    wf = ProjectDevelopmentWorkflow()

    async def run():
        return await wf.execute(make_architecture_analysis(), output_dir=output_dir)

    result = asyncio.get_event_loop().run_until_complete(run())
    assert result["status"] == "completed"
    coverage = result["steps"]["coverage"]
    assert coverage["coverage_percentage"] == 100
    # 输出文件存在
    files = os.listdir(output_dir)
    assert any(f.startswith("development_workflow_result_") for f in files)
    assert any(f.startswith("development_overview_") for f in files)

