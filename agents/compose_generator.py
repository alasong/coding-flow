import os


class ComposeGeneratorAgent:
    def __init__(self, name: str = "Compose生成"):
        self.name = name

    async def generate(self, output_dir: str, rel_code_path: str):
        docker_dir = os.path.join(output_dir, "docker")
        os.makedirs(docker_dir, exist_ok=True)
        compose = (
            "version: '3.8'\n"
            "services:\n"
            "  app:\n"
            f"    build: {rel_code_path}\n"
            "    ports:\n"
            "      - '8000:8000'\n"
            "    environment:\n"
            "      - ENV=dev\n"
        )
        with open(os.path.join(docker_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
            f.write(compose)

