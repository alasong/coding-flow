from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config import DEV_MODEL

class APISpecGeneratorAgent(BaseAgent):
    def __init__(self, name: str = "API规范生成专家", model_config_name: str = "api_spec_generator"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=DEV_MODEL)

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os, json
        
        # 离线逻辑
        if not getattr(self, "model", None):
            return await self._generate_offline(software_units, work_packages, output_dir)
            
        # 筛选 API 类型的单元
        api_units = [u for u in software_units if u.get("type") == "api"]
        
        prompt = f"""
        请根据以下软件单元定义，生成标准的 OpenAPI 3.0 JSON 规范。

        【API单元列表】
        {json.dumps(api_units, ensure_ascii=False, indent=2)}

        请直接返回合法的 JSON 字符串，不要包含 Markdown 格式标记。
        必须包含：
        - openapi: "3.0.0"
        - info: {{ title: "Project API", version: "1.0.0" }}
        - paths: 包含所有 API 单元定义的路径和方法
        """

        try:
            response = await self.model([{"role": "user", "content": prompt}])
            content = await self._process_model_response(response)
            
            # 提取 JSON
            import re
            code_block_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if code_block_match:
                spec = json.loads(code_block_match.group(1))
            else:
                spec = json.loads(content)
                
            base = os.path.join(output_dir, "project_code")
            os.makedirs(base, exist_ok=True)
            with open(os.path.join(base, "openapi.json"), "w", encoding="utf-8") as f:
                json.dump(spec, f, ensure_ascii=False, indent=2)
                
            return {"apis": ["openapi.json"], "created": True}
            
        except Exception as e:
            return await self._generate_offline(software_units, work_packages, output_dir)

    async def _generate_offline(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
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
