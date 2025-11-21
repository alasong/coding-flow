import os


class CDConfiguratorAgent:
    def __init__(self, name: str = "CD配置"):
        self.name = name

    async def generate(self, output_dir: str, mode: str):
        wdir = os.path.join(output_dir, "cd")
        os.makedirs(wdir, exist_ok=True)
        with open(os.path.join(wdir, "deploy.yml"), "w", encoding="utf-8") as f:
            f.write("name: Deploy\non: [workflow_dispatch]\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - uses: actions/setup-python@v4\n        with:\n          python-version: '3.x'\n      - run: echo 'build and deploy'\n")

