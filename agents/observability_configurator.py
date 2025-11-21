import os


class ObservabilityConfiguratorAgent:
    def __init__(self, name: str = "可观测性配置"):
        self.name = name

    async def generate(self, output_dir: str):
        odir = os.path.join(output_dir, "observability")
        os.makedirs(os.path.join(odir, "grafana_dashboards"), exist_ok=True)
        with open(os.path.join(odir, "prometheus.yml"), "w", encoding="utf-8") as f:
            f.write("global:\n  scrape_interval: 15s\nscrape_configs: []\n")

