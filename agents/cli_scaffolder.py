from typing import List, Dict, Any


class CLIScaffolderAgent:
    def __init__(self, name: str = "CLI脚手架生成"):
        self.name = name

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os
        base = os.path.join(output_dir, "project_code")
        with open(os.path.join(base, "cli.py"), "w", encoding="utf-8") as f:
            f.write(
                "import typer\nimport requests\napp = typer.Typer()\n\n"
                "@app.command()\n"
                "def health(url: str = 'http://localhost:8000/health'):\n"
                "    r = requests.get(url)\n"
                "    typer.echo(r.json())\n\n"
                "if __name__ == '__main__':\n"
                "    app()\n"
            )
        # 追加CLI依赖
        req = os.path.join(base, "requirements.txt")
        with open(req, "a", encoding="utf-8") as f:
            f.write("typer\nrequests\n")
        return {"cli": ["cli.py"]}

