import os


class EnvConfigAgent:
    def __init__(self, name: str = "环境配置生成"):
        self.name = name

    async def generate(self, output_dir: str):
        envdir = os.path.join(output_dir, "env")
        os.makedirs(envdir, exist_ok=True)
        for n in ["dev", "staging", "prod"]:
            with open(os.path.join(envdir, f"{n}.env"), "w", encoding="utf-8") as f:
                f.write("ENV=" + n + "\nPORT=8000\n")
        with open(os.path.join(envdir, "secrets.example"), "w", encoding="utf-8") as f:
            f.write("SECRET_KEY=\nDATABASE_URL=\n")

