#!/usr/bin/env python3
"""
需求分析工作流系统完整演示
展示get_workflow_status方法的使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow.requirement_workflow import RequirementAnalysisWorkflow

def demo_workflow_system():
    """演示完整的工作流系统"""
    print("=" * 60)
    print("需求分析工作流系统演示")
    print("=" * 60)
    
    # 创建工作流实例
    print("1. 创建工作流实例...")
    workflow = RequirementAnalysisWorkflow()
    print("✓ 工作流实例创建成功")
    
    # 获取初始状态
    print("\n2. 获取工作流初始状态...")
    initial_status = workflow.get_workflow_status()
    print(f"   已初始化Agent数量: {initial_status['agents_initialized']}")
    print(f"   Agent列表: {list(initial_status['agents_status'].keys())}")
    print(f"   工作流数据大小: {initial_status['workflow_data_size']} 字节")
    
    # 运行需求分析
    print("\n3. 运行需求分析工作流...")
    sample_requirement = """
    开发一个在线学习管理系统，包含以下功能：
    - 用户注册登录和个人资料管理
    - 课程创建和管理（教师角色）
    - 视频课程播放和进度跟踪
    - 作业发布和提交系统
    - 在线考试和自动评分
    - 学习讨论区
    - 成绩管理和报告生成
    - 移动端适配
    """
    
    print("   需求描述:", sample_requirement[:100] + "...")
    result = workflow.run(sample_requirement)
    
    if result['status'] == 'success':
        print("✓ 需求分析完成")
        print(f"   输出文件: {result['output_file']}")
    else:
        print(f"✗ 需求分析失败: {result['error']}")
        return
    
    # 获取运行后的状态
    print("\n4. 获取运行后的工作流状态...")
    final_status = workflow.get_workflow_status()
    print(f"   已初始化Agent数量: {final_status['agents_initialized']}")
    print(f"   工作流数据大小: {final_status['workflow_data_size']} 字节")
    
    # 状态变化分析
    print("\n5. 状态变化分析...")
    data_size_increase = final_status['workflow_data_size'] - initial_status['workflow_data_size']
    print(f"   工作流数据大小增加: {data_size_increase} 字节")
    print(f"   数据增长率: {(data_size_increase / max(initial_status['workflow_data_size'], 1) * 100):.1f}%")
    
    # 展示结果摘要
    print("\n6. 需求分析结果摘要...")
    if 'results' in result:
        results = result['results']
        if 'collected_requirements' in results:
            print("   ✓ 需求收集完成")
        if 'analysis_results' in results:
            print("   ✓ 需求分析完成")
        if 'validation_results' in results:
            print("   ✓ 需求验证完成")
        if 'requirement_document' in results:
            print("   ✓ 需求文档生成完成")
    
    print("\n" + "=" * 60)
    print("演示完成！get_workflow_status方法工作正常")
    print("=" * 60)

if __name__ == "__main__":
    demo_workflow_system()