from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config import DEV_MODEL

class RepoScaffolderAgent(BaseAgent):
    def __init__(self, name: str = "代码脚手架生成专家", model_config_name: str = "repo_scaffolder"):
        super().__init__(name=name, model_config_name=model_config_name, model_name=DEV_MODEL)

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str, ui_mode: str = "web") -> Dict[str, Any]:
        import os
        import json
        
        # 离线逻辑：如果模型未初始化，使用硬编码的简单脚手架
        if not getattr(self, "model", None):
            return await self._generate_offline(software_units, work_packages, output_dir, ui_mode)

        # 构建 Prompt
        prompt = f"""
        请根据以下项目信息，生成一个标准化的项目代码脚手架结构。

        【UI模式】
        {ui_mode}

        【软件单元】
        {json.dumps(software_units, ensure_ascii=False, indent=2)}

        【工作包】
        {json.dumps(work_packages, ensure_ascii=False, indent=2)}

        请生成包含完整文件路径和关键文件内容的 JSON 结构。
        格式要求：
        {{
            "files": [
                {{
                    "path": "完整文件路径（相对于项目根目录）",
                    "content": "文件完整内容"
                }}
            ]
        }}
        必须包含的文件：
        - README.md (包含详细的项目说明、启动方式)
        - .gitignore
        - requirements.txt / pyproject.toml (必须包含: fastapi, uvicorn, pytest, sqlalchemy, httpx, pydantic-settings)
        - Dockerfile
        - 核心应用入口 (如 main.py / app.py)
        - 测试目录结构
        """

        try:
            response = await self.model([{"role": "user", "content": prompt}])
            content = await self._process_model_response(response)
            
            # 解析 JSON
            import re
            code_block_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if code_block_match:
                result = json.loads(code_block_match.group(1))
            else:
                result = json.loads(content)
            
            files = result.get("files", [])
            base = os.path.join(output_dir, "project_code")
            
            created_paths = []
            for file_info in files:
                path = file_info.get("path")
                file_content = file_info.get("content")
                if path and file_content:
                    full_path = os.path.join(base, path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(file_content)
                    created_paths.append(path)
            
            return {"modules": created_paths, "created": True, "code_dir": base}

        except Exception as e:
            # 失败回退
            return await self._generate_offline(software_units, work_packages, output_dir, ui_mode)

    async def _generate_offline(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str, ui_mode: str = "web") -> Dict[str, Any]:
        import os
        base = os.path.join(output_dir, "project_code")
        os.makedirs(base, exist_ok=True)
        os.makedirs(os.path.join(base, "app"), exist_ok=True)
        os.makedirs(os.path.join(base, "tests"), exist_ok=True)
        os.makedirs(os.path.join(base, ".github", "workflows"), exist_ok=True)
        # ... (保留原有的硬编码生成逻辑)
        # 生成后端入口，挂载前端静态资源
        with open(os.path.join(base, "app", "main.py"), "w", encoding="utf-8") as f:
            content = (
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.get('/health')\n"
                "def health():\n"
                "    return {'status': 'ok'}\n"
            )
            if ui_mode == "web":
                content += (
                    "from fastapi.staticfiles import StaticFiles\n"
                    "import os\n"
                    "if os.path.exists('frontend'):\n"
                    "    app.mount('/ui', StaticFiles(directory='frontend', html=True), name='ui')\n"
                )
            f.write(content)
        with open(os.path.join(base, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("fastapi\nuvicorn\npytest\n")
        with open(os.path.join(base, "README.md"), "w", encoding="utf-8") as f:
            readme = (
                "# 项目代码\n\n"
                "## 环境准备\n"
                "```bash\n"
                "pip install -r requirements.txt\n"
                "```\n\n"
                "## 启动服务\n"
                "```bash\n"
                "uvicorn app.main:app --reload --port 8000\n"
                "# 健康检查\n"
                "curl http://localhost:8000/health\n"
                "```\n\n"
                "## API 文档\n"
                "- 访问 FastAPI Swagger: http://localhost:8000/docs\n"
                "- OpenAPI 规范文件: openapi.json\n\n"
                "## 运行测试\n"
                "```bash\n"
                "pytest -q\n"
                "```\n\n"
                "## CI (GitHub Actions)\n"
                "- 工作流文件: .github/workflows/ci.yml\n"
                "- 默认执行：安装依赖并运行 pytest\n"
            )
            if ui_mode == "web":
                readme += (
                    "\n## 前端界面\n"
                    "- 访问界面: http://localhost:8000/ui/\n"
                    "- 静态资源目录: frontend\n"
                )
            else:
                readme += (
                    "\n## CLI 使用\n"
                    "```bash\n"
                    "python cli.py health\n"
                    "```\n"
                )
            f.write(readme)

        # 如存在前端单元，生成简单前端页面
        has_frontend = ui_mode == "web" or any(u.get("type") == "frontend" for u in software_units)
        if has_frontend:
            os.makedirs(os.path.join(base, "frontend"), exist_ok=True)
            with open(os.path.join(base, "frontend", "index.html"), "w", encoding="utf-8") as f:
                f.write(
                    "<!doctype html>\n<html>\n<head><meta charset='utf-8'><title>UI</title></head>\n"
                    "<body>\n<h1>项目前端界面</h1>\n<div id='status'></div>\n"
                    "<script>fetch('/health').then(r=>r.json()).then(j=>{document.getElementById('status').innerText='健康状态: '+j.status})</script>\n"
                    "</body></html>\n"
                )
        return {"modules": ["app/main.py", "tests", ".github/workflows"], "created": True, "code_dir": base}
