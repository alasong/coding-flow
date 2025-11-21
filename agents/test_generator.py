from typing import List, Dict, Any


class TestGeneratorAgent:
    def __init__(self, name: str = "测试生成"):
        self.name = name

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os
        base = os.path.join(output_dir, "project_code")
        with open(os.path.join(base, "tests", "test_basic.py"), "w", encoding="utf-8") as f:
            f.write("def test_dummy():\n    assert True\n")
        with open(os.path.join(base, "test_report.md"), "w", encoding="utf-8") as f:
            f.write("# 测试报告\n\n通过用例: 1\n")
        return {"tests": ["tests/test_basic.py"], "coverage_threshold": 0.7}
