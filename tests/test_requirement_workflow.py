
import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from workflow.requirement_workflow import RequirementAnalysisWorkflow
from utils.common import setup_logging

# 配置日志
setup_logging("INFO")
logger = logging.getLogger(__name__)

async def test_requirement_workflow():
    """测试需求分析工作流"""
    print("\n" + "="*60)
    print("需求分析功能独立调测")
    print("="*60)
    
    # 模拟输入数据
    input_data = """
    我想开发一个简单的待办事项管理应用（To-Do List）。
    主要功能包括：
    1. 用户可以添加新的待办事项
    2. 用户可以标记事项为已完成
    3. 用户可以删除事项
    4. 数据需要持久化存储
    5. 界面要简洁美观
    """
    
    print(f"\n[测试输入]:\n{input_data}")
    
    try:
        # 初始化工作流
        workflow = RequirementAnalysisWorkflow()
        
        # 运行工作流 (交互模式设置为True以测试评审环节)
        # 注意：在自动化测试中通常设置为False，这里为了演示设为True
        # 但为了避免阻塞，我们模拟非交互模式或提供预设输入
        print("\n[开始执行工作流]...")
        result = await workflow.run(input_data, output_dir="tests/output", interactive=False)
        
        # 验证结果
        print("\n" + "="*60)
        print("执行结果验证")
        print("="*60)
        
        if result["status"] == "success":
            print("[SUCCESS] 工作流执行成功")
            
            # 检查关键输出
            results = result.get("results", {})
            
            # 1. 检查收集的需求
            collected = results.get("collected_requirements", {})
            print(f"\n1. 收集到的需求:")
            print(f"   - 功能需求数: {len(collected.get('functional_requirements', []))}")
            print(f"   - 非功能需求数: {len(collected.get('non_functional_requirements', []))}")
            
            # 2. 检查分析结果
            analysis = results.get("analysis_results", {})
            print(f"\n2. 可行性分析:")
            print(f"   - 分析内容长度: {len(str(analysis.get('feasibility_analysis', '')))}")
            
            # 3. 检查评审要点
            review_points = results.get("review_points", [])
            print(f"\n3. 关键评审要点 ({len(review_points)}个):")
            for i, point in enumerate(review_points[:3]):
                print(f"   - {point}")
            
            # 4. 检查验证结果
            validation = results.get("validation_results", {})
            print(f"\n4. 验证结果:")
            print(f"   - 正确性验证: {len(str(validation.get('correctness', '')))} 字符")
            print(f"   - 完整性验证: {len(str(validation.get('completeness', '')))} 字符")
            print(f"   - 一致性验证: {len(str(validation.get('consistency', '')))} 字符")
            print(f"   - 测试用例生成: {len(str(validation.get('test_cases', '')))} 字符")
            
            # 5. 检查生成的文档
            doc = results.get("requirement_document", "")
            print(f"\n5. 需求文档生成:")
            print(f"   - 文档长度: {len(doc)} 字符")
            
            print(f"\n详细输出文件: {result.get('output_file')}")
            
            # 6. 检查验证报告文件
            import glob
            report_files = glob.glob("tests/output/requirement_validation_report_*.md")
            if report_files:
                print(f"\n[SUCCESS] 找到验证报告文件: {report_files[0]}")
            else:
                print("\n[FAILED] 未找到验证报告文件")
                
            # 7. 验证交付件（Artifacts）与输出件（Outputs）的区别
            artifacts = result.get("artifacts", {})
            outputs = result.get("outputs", {})
            
            print(f"\n7. 交付件与输出件验证:")
            if "validation_report" in outputs:
                 print("   [SUCCESS] validation_report 存在于 outputs 中")
            else:
                 print("   [FAILED] validation_report 不存在于 outputs 中")
                 
            if "validation_report" not in artifacts:
                 print("   [SUCCESS] validation_report 不存在于 artifacts 中 (符合要求)")
            else:
                 print("   [FAILED] validation_report 存在于 artifacts 中 (不符合要求)")
            
        else:
            print(f"[FAILED] 工作流执行失败: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"测试过程发生错误: {e}")
        print(f"[ERROR] 测试过程发生错误: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_requirement_workflow())
    except KeyboardInterrupt:
        print("\n测试被中断")
