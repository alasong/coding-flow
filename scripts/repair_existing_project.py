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

async def run_repair(args):
    # 将项目根目录添加到 sys.path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)

    from workflow.development_execution_workflow import DevelopmentExecutionWorkflow
    
    workflow = DevelopmentExecutionWorkflow()
    return await workflow.repair_existing(
        output_dir=args.output_dir,
        integration_dir=args.integration_dir,
        development_dir=args.development_dir
    )

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    
    # 解决 DeprecationWarning
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    result = loop.run_until_complete(run_repair(args))
    
    status = result.get("status")
    print(f"修复完成，状态: {status}")
    if status != "completed":
        print(f"错误信息: {result.get('error')}")
        # 尝试打印最后的验证结果，看看具体失败原因
        verify_res = result.get('final_result', {}).get('verify', {})
        if verify_res:
             print(f"最终验证输出: {verify_res.get('output', '')[:500]}...") # 打印前500字符

    return 0 if status == "completed" else 1

if __name__ == "__main__":
    sys.exit(main())
