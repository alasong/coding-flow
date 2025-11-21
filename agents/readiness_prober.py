import os


class ReadinessProberAgent:
    def __init__(self, name: str = "探针生成"):
        self.name = name

    async def generate(self, output_dir: str):
        sdir = os.path.join(output_dir, "scripts")
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, "check_health.sh"), "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env bash\ncurl -s http://localhost:8000/health\n")
        with open(os.path.join(sdir, "check_health.ps1"), "w", encoding="utf-8") as f:
            f.write("Invoke-RestMethod -Uri http://localhost:8000/health\n")

