#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="基于执行哲学重新处理项目分解交付件")
    parser.add_argument("--input-file", required=True, help="development_artifacts 或 development_workflow_result 文件路径")
    parser.add_argument("--output-file", default="", help="输出文件路径（默认生成 *_refined_时间戳.json）")
    return parser


def resolve_output_path(input_file: str, output_file: str) -> str:
    if output_file:
        return output_file
    base_dir = os.path.dirname(input_file)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(base_dir, f"development_artifacts_refined_{ts}.json")


async def refine(input_file: str, output_file: str) -> None:
    from agents.work_package_planner import WorkPackagePlannerAgent
    from agents.unit_workpackage_matcher import UnitToWorkPackageMatcherAgent
    from agents.coverage_auditor import CoverageAuditorAgent
    from agents.concurrency_orchestrator import ConcurrencyOrchestratorAgent
    from agents.dev_plan_generator import DevPlanGeneratorAgent
    from agents.dev_document_exporter import DevDocumentExporterAgent

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "software_units" in data:
        software_units = data.get("software_units", [])
    elif "final_result" in data:
        software_units = data.get("final_result", {}).get("software_units", [])
    else:
        raise ValueError("无法从输入文件提取 software_units")

    planner = WorkPackagePlannerAgent()
    matcher = UnitToWorkPackageMatcherAgent()
    auditor = CoverageAuditorAgent()
    orchestrator = ConcurrencyOrchestratorAgent()
    plan_generator = DevPlanGeneratorAgent()
    exporter = DevDocumentExporterAgent()

    packages = await planner.plan(software_units)
    match_out = await matcher.match(software_units, packages)
    packages = match_out["work_packages"]

    coverage = await auditor.audit(software_units, packages)
    concurrency = await orchestrator.plan_batches(packages, software_units)
    dev_plans = await plan_generator.generate_offline(packages)
    docs = await exporter.export(software_units, packages, coverage, concurrency, dev_plans)

    artifacts = {
        "software_units": software_units,
        "work_packages": packages,
        "concurrency_plan": concurrency,
        "dev_plans": dev_plans,
        "documents": docs
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(artifacts, f, ensure_ascii=False, indent=2)


def main() -> int:
    args = build_parser().parse_args()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)
    output_path = resolve_output_path(args.input_file, args.output_file)
    asyncio.run(refine(args.input_file, output_path))
    print(f"已生成新交付件: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
