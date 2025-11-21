from typing import List, Dict, Any


class APISpecGeneratorAgent:
    def __init__(self, name: str = "API规范生成"):
        self.name = name

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os, json
        base = os.path.join(output_dir, "project_code")
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {"/health": {"get": {"responses": {"200": {"description": "OK"}}}}}
        }
        with open(os.path.join(base, "openapi.json"), "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        return {"apis": ["openapi.json"], "created": True}
