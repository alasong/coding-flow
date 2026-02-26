import asyncio
import os
import sys
import json
import logging
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from workflow.requirement_workflow import RequirementAnalysisWorkflow
from workflow.architecture_workflow import ArchitectureDesignWorkflow
from utils.common import setup_logging

# 配置日志
setup_logging("INFO")
logger = logging.getLogger(__name__)

async def test_requirement_architecture_integration():
    """测试“需求分析”+“架构设计”集成流程"""
    print("\n" + "="*60)
    print("集成测试: 需求分析 -> 架构设计")
    print("="*60)
    
    output_dir = "tests/output/integration_test"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 模拟输入数据
    input_data = """
    我想开发一个企业级的文档管理系统（DMS）。
    主要功能包括：
    1. 用户可以上传、下载、预览各种格式的文档（PDF, Word, 图片）。
    2. 支持文档的版本管理，保留历史版本。
    3. 具有严格的权限控制体系（RBAC），支持部门、角色、用户维度的权限设置。
    4. 支持全文检索，可以搜索文档内容。
    5. 需要记录详细的操作日志以满足审计要求。
    6. 系统需支持高并发访问（1000+并发），且保证数据的高可用性。
    """
    
    print(f"\n[Step 1] 启动需求分析工作流...")
    print(f"输入需求:\n{input_data}")
    
    try:
        # ==========================================
        # 阶段 1: 需求分析
        # ==========================================
        req_workflow = RequirementAnalysisWorkflow()
        req_result = await req_workflow.run(input_data, output_dir=output_dir, interactive=False)
        
        if req_result["status"] != "success":
            print(f"[FAILED] 需求分析失败: {req_result.get('error')}")
            return
            
        req_artifacts = req_result.get("artifacts", {})
        print("\n[SUCCESS] 需求分析完成")
        print(f"生成的交付件包含: {list(req_artifacts.keys())}")
        print(f"需求条目数: {len(req_artifacts.get('requirement_entries', []))}")
        
        # ==========================================
        # 阶段 2: 架构设计
        # ==========================================
        print(f"\n[Step 2] 启动架构设计工作流...")
        
        arch_workflow = ArchitectureDesignWorkflow()
        
        # 将需求分析的交付件作为输入
        arch_result = await arch_workflow.run(req_artifacts, output_dir=output_dir)
        
        if arch_result["status"] != "completed":
            print(f"[FAILED] 架构设计失败: {arch_result.get('error')}")
            return
            
        print("\n[SUCCESS] 架构设计完成")
        
        # ==========================================
        # 结果验证
        # ==========================================
        print("\n" + "="*60)
        print("集成测试结果验证")
        print("="*60)
        
        final_result = arch_result.get("final_result", {})
        arch_design = final_result.get("architecture_design", {})
        
        # 验证系统组件
        components = arch_design.get("system_architecture", {}).get("components", [])
        print(f"\n1. 系统组件 ({len(components)}个):")
        for comp in components:
            print(f"   - {comp.get('name')}: {comp.get('description')}")
            
        # 验证技术栈
        tech_stack = arch_design.get("technology_stack", {})
        print(f"\n2. 技术栈选型:")
        print(f"   - 前端: {tech_stack.get('frontend', '未定义')}")
        print(f"   - 后端: {tech_stack.get('backend', '未定义')}")
        print(f"   - 数据库: {tech_stack.get('database', '未定义')}")
        
        # 验证API设计
        api_design = arch_design.get("api_architecture", {})
        endpoints = api_design.get("api_endpoints", [])
        print(f"\n3. API 设计 ({len(endpoints)}个端点):")
        if endpoints:
            print(f"   - 示例: {endpoints[0].get('method')} {endpoints[0].get('path')}")
            
        # 验证文档生成
        docs = final_result.get("technical_documents", {})
        print(f"\n4. 生成文档:")
        for doc_type, content in docs.items():
            print(f"   - {doc_type}: {len(content)} 字符")
            
        # 验证文件输出
        import glob
        generated_files = glob.glob(f"{output_dir}/*")
        print(f"\n5. 输出文件 ({len(generated_files)}个):")
        for f in generated_files:
            print(f"   - {os.path.basename(f)}")
            
        # 检查是否生成了标准化的架构交付件
        arch_artifacts_files = glob.glob(f"{output_dir}/architecture_artifacts_*.json")
        if arch_artifacts_files:
            print(f"\n[SUCCESS] 找到架构交付件: {arch_artifacts_files[0]}")
        else:
            print(f"\n[WARNING] 未找到架构交付件 (architecture_artifacts_*.json)")

    except Exception as e:
        logger.error(f"集成测试发生错误: {e}")
        print(f"[ERROR] 测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_requirement_architecture_integration())
    except KeyboardInterrupt:
        print("\n测试被中断")
