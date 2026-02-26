
import asyncio
import os
import sys
import json
import logging
import glob

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from workflow.development_execution_workflow import DevelopmentExecutionWorkflow

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dev_execution_single_step():
    """测试“项目开发执行”工作流（单步调试）"""
    print("\n" + "="*60)
    print("单步测试: 项目开发执行 (基于现有Artifacts)")
    print("="*60)
    
    # 定义输入和输出目录
    # 修正：根据脚本运行位置，使用正确的相对路径
    # 由于脚本位于 coding-flow/tests/，project_root 是 coding-flow
    req_arch_dir = os.path.join(project_root, "tests/output/integration_test")
    dev_plan_dir = os.path.join(project_root, "tests/output/development_test")
    output_dir = os.path.join(project_root, "tests/output/development_execution_test")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"查找路径: {req_arch_dir}")
    
    # 1. 查找并加载最新的需求分析结果
    req_files = sorted(glob.glob(f"{req_arch_dir}/requirement_analysis_result_*.json"), reverse=True)
    if not req_files:
        print(f"[ERROR] 未找到需求分析交付件，请先运行相关测试")
        return
    req_file = req_files[0]
    print(f"加载需求分析: {os.path.basename(req_file)}")
    with open(req_file, "r", encoding="utf-8") as f:
        req_data = json.load(f)
        requirements = req_data.get("results", {}).get("validation_summary", {})

    # 2. 查找并加载最新的架构设计结果
    arch_files = sorted(glob.glob(f"{req_arch_dir}/architecture_artifacts_*.json"), reverse=True)
    if not arch_files:
        print(f"[ERROR] 未找到架构设计交付件，请先运行相关测试")
        return
    arch_file = arch_files[0]
    print(f"加载架构设计: {os.path.basename(arch_file)}")
    with open(arch_file, "r", encoding="utf-8") as f:
        arch_data = json.load(f)
        architecture = arch_data.get("architecture_design", {}).get("system_architecture", {})

    # 3. 查找并加载最新的项目分解结果
    # 注意：这里我们优先查找 development_artifacts_*.json，如果没有，则查找 development_workflow_result_*.json
    dev_files = sorted(glob.glob(f"{dev_plan_dir}/development_artifacts_*.json"), reverse=True)
    if not dev_files:
        dev_files = sorted(glob.glob(f"{dev_plan_dir}/development_workflow_result_*.json"), reverse=True)
    
    if not dev_files:
        print(f"[ERROR] 未找到项目分解交付件，请先运行 tests/test_development_single_step.py")
        return
    
    dev_file = dev_files[0]
    print(f"加载项目分解: {os.path.basename(dev_file)}")
    
    with open(dev_file, "r", encoding="utf-8") as f:
        dev_data = json.load(f)
        # 兼容两种格式
        if "software_units" in dev_data and "work_packages" in dev_data:
             decomposition_result = {"final_result": dev_data}
        elif "final_result" in dev_data:
             decomposition_result = dev_data
        else:
             print("[ERROR] 项目分解文件格式无法识别")
             return

    # 4. 执行工作流
    print(f"\n[Step 1] 启动项目开发执行工作流...")
    
    workflow = DevelopmentExecutionWorkflow()
    
    try:
        result = await workflow.execute(
            decomposition_result=decomposition_result,
            requirements=requirements,
            architecture=architecture,
            output_dir=output_dir
        )
        
        if result["status"] != "completed":
             print(f"[FAILED] 项目开发执行失败: {result.get('error')}")
             return

        print("\n[SUCCESS] 项目开发执行完成")
        
        # 5. 验证结果
        exec_dir = os.path.join(output_dir, "project_code")
        print(f"\n[Step 2] 验证生成文件 (目录: {exec_dir})...")
        
        # 打印验证报告路径
        verify_report_path = os.path.join(exec_dir, "verify_report.md")
        if os.path.exists(verify_report_path):
            print(f"\n[INFO] 验证报告位置: {verify_report_path}")
            # 读取并打印报告的前几行
            try:
                with open(verify_report_path, "r", encoding="utf-8") as f:
                    print("--- 验证报告摘要 ---")
                    for _ in range(5):
                        line = f.readline()
                        if not line: break
                        print(line.strip())
                    print("----------------------")
            except Exception as e:
                print(f"[WARN] 无法读取验证报告: {e}")
        
        # 验证 Git 分支创建
        print(f"\n[Step 3] 验证 Git 分支...")
        try:
             import subprocess
             result = subprocess.run(["git", "branch"], cwd=exec_dir, capture_output=True, text=True)
             print(f"当前分支:\n{result.stdout}")
             if "develop" in result.stdout:
                  print("[SUCCESS] 分支 develop 创建成功")
        except Exception as e:
             print(f"[WARN] Git 验证失败: {e}")

        if os.path.exists(exec_dir):
            files = []
            for root, _, filenames in os.walk(exec_dir):
                for filename in filenames:
                    rel_path = os.path.relpath(os.path.join(root, filename), exec_dir)
                    files.append(rel_path)
            
            print(f"共生成 {len(files)} 个文件:")
            for f in sorted(files):
                print(f"   - {f}")
                
            # 关键文件检查
            key_files = ["README.md", "requirements.txt", "openapi.json"]
            missing = [f for f in key_files if f not in files and not any(f in path for path in files)]
            
            if not missing:
                 print("\n[SUCCESS] 关键文件验证通过")
            else:
                 print(f"\n[WARNING] 缺失关键文件: {missing}")
        else:
            print(f"\n[ERROR] 代码目录未生成: {exec_dir}")

    except Exception as e:
        logger.error(f"单步测试发生错误: {e}")
        print(f"[ERROR] 测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_dev_execution_single_step())
    except KeyboardInterrupt:
        print("\n测试被中断")
