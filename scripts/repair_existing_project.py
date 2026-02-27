#!/usr/bin/env python3
import argparse
import asyncio
import os
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="修复已生成项目（依赖交付件必须存在）")
    parser.add_argument("--output-dir", required=True, help="开发执行输出目录（包含 project_code）")
    parser.add_argument("--integration-dir", required=True, help="integration_test 交付件目录")
    parser.add_argument("--development-dir", required=True, help="development_test 交付件目录")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)

    from workflow.development_execution_workflow import DevelopmentExecutionWorkflow

    async def run():
        workflow = DevelopmentExecutionWorkflow()
        return await workflow.repair_existing(
            output_dir=args.output_dir,
            integration_dir=args.integration_dir,
            development_dir=args.development_dir
        )

    result = asyncio.get_event_loop().run_until_complete(run())
    status = result.get("status")
    print(f"修复完成，状态: {status}")
    if status != "completed":
        print(f"错误信息: {result.get('error')}")
    return 0 if status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
