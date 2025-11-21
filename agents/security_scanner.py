import os


class SecurityScannerAgent:
    def __init__(self, name: str = "安全扫描"):
        self.name = name

    async def generate(self, output_dir: str):
        rdir = os.path.join(output_dir, "reports")
        os.makedirs(rdir, exist_ok=True)
        with open(os.path.join(rdir, "security_scan.md"), "w", encoding="utf-8") as f:
            f.write("# 安全扫描\n\n扫描结果占位\n")

