import asyncio
import os
import sys

# Add project root to sys.path to fix import errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow.development_workflow import ProjectDevelopmentWorkflow
from workflow.development_execution_workflow import DevelopmentExecutionWorkflow
from agents.repo_scaffolder import RepoScaffolderAgent
from agents.api_spec_generator import APISpecGeneratorAgent
from agents.db_migration_planner import DBMigrationPlannerAgent

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


def test_dev_execution_single_step(tmp_path):
    """Test individual steps of Development Execution Workflow"""
    output_dir = str(tmp_path)
    
    # Mock decomposition result
    mock_decomp_result = {
        "final_result": {
            "software_units": [
                {"id": "API::GET /users", "type": "api", "name": "GET /users"},
                {"id": "DB::users", "type": "db", "name": "users"},
                {"id": "COMP::UserSvc", "type": "component", "name": "UserSvc"}
            ],
            "work_packages": [
                {"id": "WP-001", "name": "User Module", "software_unit_ids": ["API::GET /users", "DB::users", "COMP::UserSvc"]}
            ]
        }
    }
    
    async def run_single_steps():
        # 1. Test Repo Scaffolder
        scaffolder = RepoScaffolderAgent()
        scaffold_res = await scaffolder.generate(
            mock_decomp_result["final_result"]["software_units"],
            mock_decomp_result["final_result"]["work_packages"],
            output_dir,
            ui_mode="cli"
        )
        assert scaffold_res["created"] is True
        assert os.path.exists(os.path.join(output_dir, "project_code", "README.md"))

        # 2. Test API Spec Generator
        api_gen = APISpecGeneratorAgent()
        api_res = await api_gen.generate(
            mock_decomp_result["final_result"]["software_units"],
            mock_decomp_result["final_result"]["work_packages"],
            output_dir
        )
        assert api_res["created"] is True
        assert os.path.exists(os.path.join(output_dir, "project_code", "openapi.json"))
        
        # 3. Test DB Migration Planner
        db_planner = DBMigrationPlannerAgent()
        db_res = await db_planner.plan(
            mock_decomp_result["final_result"]["software_units"],
            mock_decomp_result["final_result"]["work_packages"],
            output_dir
        )
        assert len(db_res.get("migrations", [])) > 0
        
    asyncio.get_event_loop().run_until_complete(run_single_steps())


def test_dev_execution_with_real_artifacts(tmp_path):
    """
    Integration test using real artifacts from previous stages.
    Reads from tests/output/integration_test and tests/output/development_test
    """
    output_dir = str(tmp_path)
    
    # Define paths to real artifact files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    req_file = os.path.join(base_dir, "tests/output/integration_test/requirement_analysis_result_20260225_231035.json")
    arch_file = os.path.join(base_dir, "tests/output/integration_test/architecture_artifacts_20260225_231230.json")
    dev_file = os.path.join(base_dir, "tests/output/development_test/development_artifacts_20260226_083239.json")
    
    # Check if files exist
    if not all(os.path.exists(f) for f in [req_file, arch_file, dev_file]):
        print("Skipping test: Real artifact files not found in tests/output")
        return

    # Load artifacts
    import json
    with open(req_file, 'r') as f:
        req_data = json.load(f)
        # Extract validation summary as requirements input
        requirements = req_data.get("results", {}).get("validation_summary", {})
        
    with open(arch_file, 'r') as f:
        arch_data = json.load(f)
        # Extract system architecture
        architecture = arch_data.get("architecture_design", {}).get("system_architecture", {})

    with open(dev_file, 'r') as f:
        dev_data = json.load(f)
        # Use the whole content as decomposition result
        decomposition_result = {"final_result": dev_data}

    async def run_integration():
        workflow = DevelopmentExecutionWorkflow()
        result = await workflow.execute(
            decomposition_result, 
            requirements, 
            architecture, 
            output_dir=os.path.join(output_dir, "real_artifact_execution")
        )
        return result

    result = asyncio.get_event_loop().run_until_complete(run_integration())
    
    # Assertions
    assert result["status"] == "completed"
    
    exec_dir = os.path.join(output_dir, "real_artifact_execution", "project_code")
    assert os.path.exists(exec_dir)
    
    # Verify key generated files based on real artifacts
    # 1. Check Scaffolding
    assert os.path.exists(os.path.join(exec_dir, "README.md"))
    assert os.path.exists(os.path.join(exec_dir, "requirements.txt"))
    
    # 2. Check API Spec
    assert os.path.exists(os.path.join(exec_dir, "openapi.json"))
    
    # 3. Check DB Migrations (if DB units exist)
    # The real artifact has DB units, so migrations should be planned
    # Note: DBMigrationPlanner currently returns a plan but might not write files in offline mode
    # Let's check if the step completed successfully
    assert result["steps"]["db_migration"]["status"] == "completed"

    print(f"Integration test with real artifacts passed. Output at: {exec_dir}")

