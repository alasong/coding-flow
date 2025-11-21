from typing import List, Dict, Any


class CIConfiguratorAgent:
    def __init__(self, name: str = "CI配置"):
        self.name = name

    async def configure(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os
        base = os.path.join(output_dir, "project_code", ".github", "workflows")
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, "ci.yml"), "w", encoding="utf-8") as f:
            f.write("name: CI\n\non: [push]\n\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: actions/setup-python@v4\n        with:\n          python-version: '3.x'\n      - run: pip install -r project_code/requirements.txt\n      - run: pytest -q\n")
        return {"workflows": [".github/workflows/ci.yml"], "lint": True}
