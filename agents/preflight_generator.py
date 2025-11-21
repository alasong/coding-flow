import os
from datetime import datetime


class PreflightGeneratorAgent:
    def __init__(self, name: str = "预检生成"):
        self.name = name

    async def generate(self, output_dir: str, rel_code_path: str):
        rdir = os.path.join(output_dir, "reports")
        sdir = os.path.join(output_dir, "scripts")
        os.makedirs(rdir, exist_ok=True)
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, "preflight.sh"), "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env bash\nset -e\ncd $(dirname $0)/..\nCODE=\"" + rel_code_path + "\"\n\nif [ ! -d \"$CODE\" ]; then echo 'code dir not found'; exit 1; fi\n\ndocker build -t app:preflight $CODE\ndocker run -d --rm -p 8000:8000 --name app_preflight app:preflight\nsleep 2\ncurl -s http://localhost:8000/health\ndocker stop app_preflight\n")
        with open(os.path.join(sdir, "preflight.ps1"), "w", encoding="utf-8") as f:
            f.write("$ErrorActionPreference = 'Stop'\n$here = Split-Path $MyInvocation.MyCommand.Path\nSet-Location (Join-Path $here '..')\n$CODE = '" + rel_code_path + "'\nif (-Not (Test-Path $CODE)) { Write-Host 'code dir not found'; exit 1 }\ndocker build -t app:preflight $CODE\ndocker run -d --rm -p 8000:8000 --name app_preflight app:preflight\nStart-Sleep -Seconds 2\nInvoke-RestMethod -Uri http://localhost:8000/health\ndocker stop app_preflight\n")
        md = ["# 部署预检", "", f"生成时间: {datetime.now().isoformat()}", "", "步骤:", "1. 构建本地镜像 app:preflight", "2. 启动容器映射端口 8000", "3. 调用 /health 验证健康", "4. 停止容器"]
        with open(os.path.join(rdir, "preflight.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        return {"scripts": ["scripts/preflight.sh", "scripts/preflight.ps1"], "report": "reports/preflight.md"}

