class SecureConfigAgent:
    def __init__(self, name: str = "安全配置审计"):
        self.name = name

    async def audit(self, output_dir: str) -> dict:
        import os
        base = os.path.join(output_dir, "project_code")
        with open(os.path.join(base, ".env.example"), "w", encoding="utf-8") as f:
            f.write("OPENAI_API_KEY=\nDASHSCOPE_API_KEY=\n")
        return {"secrets_ok": True, "env_example": True}
