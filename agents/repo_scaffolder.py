from typing import List, Dict, Any


class RepoScaffolderAgent:
    def __init__(self, name: str = "代码脚手架生成"):
        self.name = name

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str, ui_mode: str = "web") -> Dict[str, Any]:
        import os
        base = os.path.join(output_dir, "project_code")
        os.makedirs(base, exist_ok=True)
        os.makedirs(os.path.join(base, "app"), exist_ok=True)
        os.makedirs(os.path.join(base, "tests"), exist_ok=True)
        os.makedirs(os.path.join(base, ".github", "workflows"), exist_ok=True)
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
                    "app.mount('/ui', StaticFiles(directory='frontend', html=True), name='ui')\n"
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
