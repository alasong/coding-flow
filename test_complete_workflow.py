#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流测试 - 验证文档生成器重复问题修复效果
"""

import asyncio
import json
import os
from workflow.requirement_workflow import RequirementAnalysisWorkflow

async def test_complete_workflow():
    """测试完整的需求分析工作流"""
    
    # 测试输入
    test_input = "开发一个员工管理系统，包含员工信息管理、考勤管理、薪资管理等功能"
    
    print("正在测试完整的需求分析工作流...")
    print(f"测试输入: {test_input}")
    
    try:
        # 初始化工作流
        workflow = RequirementAnalysisWorkflow()
        
        # 运行完整工作流
        results = await workflow.run(test_input)
        
        print("\n=== 工作流执行结果 ===")
        
        # 检查需求收集结果
        if 'collected_requirements' in results:
            req_data = results['collected_requirements']
            functional_count = len(req_data.get('functional_requirements', []))
            non_functional_count = len(req_data.get('non_functional_requirements', []))
            constraints_count = len(req_data.get('constraints', []))
            key_features_count = len(req_data.get('key_features', []))
            
            print(f"功能需求: {functional_count} 个")
            print(f"非功能需求: {non_functional_count} 个")
            print(f"约束条件: {constraints_count} 个")
            print(f"关键功能: {key_features_count} 个")
        
        # 检查生成的文档
        output_file = results.get('output_file')
        if output_file and os.path.exists(output_file):
            print(f"\n文档已生成: {output_file}")
            
            # 读取并检查文档内容
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 只对Markdown文档进行重复检查
            if output_file.endswith('.md'):
                lines = content.split('\n')
                unique_lines = set(line.strip() for line in lines if line.strip())
                
                total_lines = len([line for line in lines if line.strip()])
                unique_count = len(unique_lines)
                duplicate_rate = ((total_lines - unique_count) / total_lines * 100) if total_lines > 0 else 0
                
                print(f"文档总有效行数: {total_lines}")
                print(f"唯一行数: {unique_count}")
                print(f"重复率: {duplicate_rate:.1f}%")
                
                # 检查文档大小
                doc_size = len(content)
                print(f"文档大小: {doc_size} 字符")
                
                # 验证重复率是否可接受
                if duplicate_rate > 20:
                    print("❌ 文档重复率过高，需要进一步修复")
                    return False
                elif doc_size > 50000:  # 50KB
                    print("❌ 文档过大，可能存在累积重复")
                    return False
                else:
                    print("✅ 需求文档生成器重复问题已修复！")
                    
                    # 显示文档前10行作为样本
                    print("\n文档样本（前10行）:")
                    sample_lines = [line for line in lines[:15] if line.strip()]
                    for i, line in enumerate(sample_lines, 1):
                        if i <= 10:
                            print(f"  {i}: {line.strip()}")
                    
                    return True
            else:
                # JSON文件仅检查大小
                print(f"JSON文件大小: {len(content)} 字符")
                if len(content) > 500000:  # 500KB
                    print("❌ JSON文件过大，可能存在累积重复问题")
                    return False
                print("✅ JSON结果文件大小正常")
                return True
        else:
            print("❌ 文档生成失败")
            return False
            
    except Exception as e:
        print(f"❌ 工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(test_complete_workflow())
    
    if result:
        print("\n✅ 完整工作流测试通过！文档生成器重复问题已成功修复。")
    else:
        print("\n❌ 完整工作流测试失败！")