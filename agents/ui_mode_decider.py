from typing import Dict, Any, List


class UIModeDeciderAgent:
    def __init__(self, name: str = "界面模式决策"):
        self.name = name

    async def decide(self, requirements: Dict[str, Any] | None, architecture: Dict[str, Any] | None) -> str:
        entries: List[Dict[str, Any]] = []
        if requirements:
            if "results" in requirements and "requirement_items" in requirements["results"]:
                entries = requirements["results"]["requirement_items"].get("requirement_entries", [])
            elif "requirement_entries" in requirements:
                entries = requirements.get("requirement_entries", [])
        text = " ".join([e.get("description", "") for e in entries]).lower()
        web_terms = ["用户", "界面", "前端", "页面", "浏览", "移动", "管理后台", "web", "ui", "docs"]
        cli_terms = ["命令行", "cli", "脚本", "批处理", "终端", "shell"]
        if any(t in text for t in web_terms):
            return "web"
        if any(t in text for t in cli_terms):
            return "cli"
        # 结合技术栈判断
        tech = None
        if architecture:
            tech = architecture.get("final_result", {}).get("architecture_design", {}).get("technology_stack") or architecture.get("technology_stack")
        if tech and tech.get("frontend"):
            return "web"
        # 默认：电商等以Web优先
        return "web"

