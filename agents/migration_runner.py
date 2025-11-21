import os


class MigrationRunnerAgent:
    def __init__(self, name: str = "迁移脚本生成"):
        self.name = name

    async def generate(self, output_dir: str):
        sdir = os.path.join(output_dir, "scripts")
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, "migrate.sh"), "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env bash\necho 'run migrations'\n")
        with open(os.path.join(sdir, "migrate.ps1"), "w", encoding="utf-8") as f:
            f.write("Write-Host 'run migrations'\n")

