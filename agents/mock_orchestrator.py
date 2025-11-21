from typing import List, Dict, Any


class MockOrchestratorAgent:
    def __init__(self, name: str = "Mock编排"):
        self.name = name

    async def prepare(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os, json
        base = os.path.join(output_dir, "project_code")
        with open(os.path.join(base, "mock_config.json"), "w", encoding="utf-8") as f:
            json.dump({"enable_mock": True}, f)
        return {"mocks": ["mock_config.json"], "flags": ["enable_mock"]}
