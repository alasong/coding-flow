#!/usr/bin/env python3
"""测试工作流状态功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow.requirement_workflow import RequirementAnalysisWorkflow

def test_workflow_status():
    """测试工作流状态获取"""
    print("创建工作流实例...")
    workflow = RequirementAnalysisWorkflow()
    
    print("获取工作流状态...")
    status = workflow.get_workflow_status()
    
    print("工作流状态信息:")
    print(f"已初始化Agent数量: {status['agents_initialized']}")
    print(f"Agent状态: {status['agents_status']}")
    print(f"工作流数据大小: {status['workflow_data_size']} 字节")
    
    # 测试运行工作流后状态是否变化
    print("\n运行示例需求分析...")
    user_input = "开发一个简单的待办事项应用"
    result = workflow.run(user_input)
    
    print("再次获取工作流状态...")
    status_after = workflow.get_workflow_status()
    
    print("运行后的状态信息:")
    print(f"已初始化Agent数量: {status_after['agents_initialized']}")
    print(f"Agent状态: {status_after['agents_status']}")
    print(f"工作流数据大小: {status_after['workflow_data_size']} 字节")
    
    if status['workflow_data_size'] < status_after['workflow_data_size']:
        print("✓ 工作流数据大小增加，状态功能正常")
    else:
        print("✗ 状态功能可能有异常")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_workflow_status()