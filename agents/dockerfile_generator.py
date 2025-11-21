import os


class DockerfileGeneratorAgent:
    def __init__(self, name: str = "Dockerfile生成"):
        self.name = name

    async def generate(self, code_dir: str, output_dir: str, ui_mode: str):
        docker_dir = os.path.join(output_dir, "docker")
        os.makedirs(docker_dir, exist_ok=True)
        content = [
            "FROM python:3.11-slim",
            "WORKDIR /app",
            "COPY ./project_code /app",
            "RUN pip install -r requirements.txt",
            "EXPOSE 8000",
            "CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]"
        ]
        with open(os.path.join(docker_dir, "Dockerfile"), "w", encoding="utf-8") as f:
            f.write("\n".join(content))

