from typing import Dict, Any, List
from datetime import datetime


class DevDocumentExporterAgent:
    def __init__(self, name: str = "开发文档导出专家"):
        self.name = name

    async def export(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], coverage_report: Dict[str, Any], concurrency_plan: Dict[str, Any], dev_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        ts = datetime.now().isoformat()
        md = []
        md.append(f"# 项目分解总览\n\n生成时间: {ts}")
        md.append(f"\n## 覆盖度\n- 总单元: {coverage_report.get('total_units',0)}\n- 已覆盖: {coverage_report.get('covered_units',0)}\n- 覆盖率: {coverage_report.get('coverage_percentage',0):.2f}%")
        md.append("\n## 并发批次")
        for i, batch in enumerate(concurrency_plan.get("batches", []), start=1):
            md.append(f"- 批次{i}: {', '.join(batch)}")
        if concurrency_plan.get("conflicts"):
            md.append("\n## 冲突包")
            for pid, res in concurrency_plan["conflicts"].items():
                md.append(f"- {pid}: 资源冲突 {', '.join(res)}")
        md.append("\n## 工作包列表")
        for p in work_packages:
            md.append(f"- {p['id']} {p['name']} 单元数:{len(p.get('software_unit_ids',[]))}")
        return {
            "development_overview_md": "\n".join(md)
        }
