import os


class HelmChartGeneratorAgent:
    def __init__(self, name: str = "Helm生成"):
        self.name = name

    async def generate(self, output_dir: str):
        charts = os.path.join(output_dir, "k8s", "charts", "app")
        os.makedirs(os.path.join(charts, "templates"), exist_ok=True)
        with open(os.path.join(charts, "Chart.yaml"), "w", encoding="utf-8") as f:
            f.write("apiVersion: v2\nname: app\nversion: 0.1.0\n")
        with open(os.path.join(charts, "values.yaml"), "w", encoding="utf-8") as f:
            f.write("replicaCount: 1\nimage: app:latest\nservice:\n  port: 8000\n")
        with open(os.path.join(charts, "templates", "deployment.yaml"), "w", encoding="utf-8") as f:
            f.write("apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app\nspec:\n  replicas: {{ .Values.replicaCount }}\n  selector:\n    matchLabels:\n      app: app\n  template:\n    metadata:\n      labels:\n        app: app\n    spec:\n      containers:\n      - name: app\n        image: {{ .Values.image }}\n        ports:\n        - containerPort: {{ .Values.service.port }}\n")

