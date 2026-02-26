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

from workflow.development_workflow import ProjectDevelopmentWorkflow
from utils.common import setup_logging

# 配置日志
setup_logging("INFO")
logger = logging.getLogger(__name__)

async def test_development_single_step():
    """测试“项目分解”工作流（单步调试）"""
    print("\n" + "="*60)
    print("单步测试: 项目分解 (基于现有Artifacts)")
    print("="*60)
    
    input_dir = "tests/output/integration_test"
    output_dir = "tests/output/development_test"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 加载最新的架构设计 Artifacts
    # 优先查找 architecture_artifacts_*.json，如果没有则尝试查找 architecture_workflow_result_*.json
    arch_files = sorted(glob.glob(f"{input_dir}/architecture_artifacts_*.json"), reverse=True)
    if not arch_files:
        arch_files = sorted(glob.glob(f"{input_dir}/architecture_workflow_result_*.json"), reverse=True)
        
    if not arch_files:
        print(f"[ERROR] 未找到架构设计交付件，请先运行 tests/test_req_arch_integration.py")
        return
        
    arch_file = arch_files[0]
    print(f"加载架构设计: {os.path.basename(arch_file)}")
    with open(arch_file, "r", encoding="utf-8") as f:
        arch_data = json.load(f)

    # 兼容处理：如果是 artifacts 格式，可能直接包含 architecture_design
    # 如果是 workflow_result 格式，则在 final_result 中
    if "architecture_design" in arch_data:
        architecture_input = arch_data
    elif "final_result" in arch_data:
         architecture_input = arch_data["final_result"].get("architecture_design", {})
    else:
        # 尝试直接作为输入
        architecture_input = arch_data

    # 2. 加载最新的需求分析 Artifacts (可选，用于补充上下文)
    req_files = sorted(glob.glob(f"{input_dir}/requirement_analysis_result_*.json"), reverse=True)
    requirements_input = None
    if req_files:
        req_file = req_files[0]
        print(f"加载需求分析: {os.path.basename(req_file)}")
        with open(req_file, "r", encoding="utf-8") as f:
            requirements_input = json.load(f).get("artifacts", {})

    # 3. 执行工作流
    print(f"\n[Step 1] 启动项目分解工作流...")
    
    dev_workflow = ProjectDevelopmentWorkflow()
    
    try:
        result = await dev_workflow.execute(
            architecture_analysis=architecture_input,
            requirements=requirements_input,
            output_dir=output_dir
        )
        
        if result["status"] != "completed":
             print(f"[FAILED] 项目分解失败: {result.get('error')}")
             return

        print("\n[SUCCESS] 项目分解完成")
        
        # 4. 验证结果
        final_result = result.get("final_result", {})
        
        # 验证软件单元
        units = final_result.get("software_units", [])
        print(f"\n1. 软件单元 ({len(units)}个):")
        for unit in units[:3]: # 只打印前3个
            print(f"   - [{unit.get('type')}] {unit.get('name')}")
        if len(units) > 3: print("   ...")
            
        # 验证工作包
        packages = final_result.get("work_packages", [])
        print(f"\n2. 工作包 ({len(packages)}个):")
        for pkg in packages[:3]:
            print(f"   - {pkg.get('id')}: {pkg.get('objective')}")
            
        # 验证并发计划
        concurrency = final_result.get("concurrency_plan", {})
        batches = concurrency.get("batches", [])
        print(f"\n3. 并发批次 ({len(batches)}批):")
        for i, batch in enumerate(batches):
            # batch 可能是字典也可能是列表，取决于返回格式
            if isinstance(batch, dict):
                count = len(batch.get('work_packages', []))
            elif isinstance(batch, list):
                count = len(batch)
            else:
                count = 0
            print(f"   - 批次 {i+1}: 包含 {count} 个工作包")
            
        # 验证文件输出
        generated_files = glob.glob(f"{output_dir}/*")
        print(f"\n4. 输出文件 ({len(generated_files)}个):")
        for f in generated_files:
            print(f"   - {os.path.basename(f)}")
            
        # 检查是否生成了标准化的开发交付件
        dev_artifacts_files = glob.glob(f"{output_dir}/development_artifacts_*.json")
        if dev_artifacts_files:
            print(f"\n[SUCCESS] 找到开发交付件: {dev_artifacts_files[0]}")
        else:
            print(f"\n[WARNING] 未找到开发交付件 (development_artifacts_*.json)")

    except Exception as e:
        logger.error(f"单步测试发生错误: {e}")
        print(f"[ERROR] 测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_development_single_step())
    except KeyboardInterrupt:
        print("\n测试被中断")
