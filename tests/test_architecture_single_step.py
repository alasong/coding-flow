import asyncio
import sys
import os
import json
from unittest.mock import patch

# Add project root to path
sys.path.append(os.getcwd())

try:
    from workflow.architecture_workflow import ArchitectureDesignWorkflow
except ImportError:
    # If running from tests directory, adjust path
    sys.path.append(os.path.dirname(os.getcwd()))
    from workflow.architecture_workflow import ArchitectureDesignWorkflow

# Mock input to select option 1 automatically
def mock_input(prompt):
    print(f"[Mock Input] Prompt: {prompt}")
    print("[Mock Input] Auto-selecting: 1")
    return "1"

async def test_architecture_workflow():
    print("Starting Architecture Workflow Test...")
    
    # Mock Requirement Artifacts (Input)
    requirements = {
        "requirement_entries": [
            {
                "id": "FR-001",
                "type": "functional",
                "description": "用户可以通过手机号注册和登录系统",
                "priority": "high",
                "status": "analyzed"
            },
            {
                "id": "FR-002",
                "type": "functional",
                "description": "用户可以创建待办事项，包含标题、描述和截止日期",
                "priority": "high",
                "status": "analyzed"
            },
            {
                "id": "FR-003",
                "type": "functional",
                "description": "用户可以将待办事项标记为完成",
                "priority": "medium",
                "status": "analyzed"
            },
            {
                "id": "NFR-001",
                "type": "non_functional",
                "description": "系统API响应时间应小于500ms",
                "priority": "high",
                "status": "analyzed"
            }
        ],
        "constraints": {
            "functional": [
                "用户可以通过手机号注册和登录系统",
                "用户可以创建待办事项，包含标题、描述和截止日期",
                "用户可以将待办事项标记为完成"
            ],
            "non_functional": [
                "系统API响应时间应小于500ms",
                "支持1000用户并发"
            ],
            "business": [
                "上线首月支持1万注册用户"
            ]
        }
    }

    workflow = ArchitectureDesignWorkflow()
    
    # Run with interactive=True to test the proposal selection logic
    # But we patch input() to automate it
    print("Initializing workflow run with interactive=True...")
    with patch('builtins.input', side_effect=mock_input):
        result = await workflow.run(requirements, interactive=True, output_dir="output/test_arch")
    
    print("\nWorkflow Execution Result:")
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'completed':
        print("Success!")
        summary = result.get('final_result', {}).get('summary')
        print("Summary:", json.dumps(summary, indent=2, ensure_ascii=False))
        
        # Check output files
        import glob
        files = glob.glob("output/test_arch/*")
        print("\nGenerated Files:")
        for f in files:
            print(f"- {f}")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_architecture_workflow())
