#!/usr/bin/env python3
"""
测试需求覆盖闭环工作流程
验证每个需求都有对应的架构设计
"""

import asyncio
import json
from workflow.architecture_workflow import ArchitectureDesignWorkflow

async def test_requirement_coverage():
    """测试需求覆盖闭环"""
    print("=== 测试需求覆盖闭环工作流程 ===")
    
    # 创建测试需求 - 使用新的格式，包含requirement_entries
    requirement_entries = [
        {
            "id": "FR001",
            "description": "用户注册功能：支持邮箱和手机号注册",
            "priority": "high",
            "type": "FR"
        },
        {
            "id": "FR002", 
            "description": "用户登录功能：支持多种登录方式",
            "priority": "high",
            "type": "FR"
        },
        {
            "id": "FR003",
            "description": "商品管理功能：支持商品CRUD操作",
            "priority": "medium", 
            "type": "FR"
        },
        {
            "id": "FR004",
            "description": "订单管理功能：支持订单创建和状态跟踪",
            "priority": "high",
            "type": "FR"
        },
        {
            "id": "FR005",
            "description": "支付功能：集成多种支付方式",
            "priority": "high",
            "type": "FR"
        },
        {
            "id": "NFR001",
            "description": "性能要求：支持1000并发用户",
            "priority": "high",
            "type": "NFR"
        },
        {
            "id": "NFR002",
            "description": "安全要求：符合等保2.0标准",
            "priority": "high", 
            "type": "NFR"
        },
        {
            "id": "NFR003",
            "description": "可用性要求：系统可用性达到99.9%",
            "priority": "medium",
            "type": "NFR"
        }
    ]
    
    test_requirements = {
        "requirement_entries": requirement_entries,
        "business_constraints": [
            "预算限制：项目预算100万",
            "时间限制：6个月内完成",
            "技术栈限制：使用云原生技术"
        ],
        "success_criteria": [
            "所有功能需求必须实现",
            "性能指标必须达标",
            "通过安全审计"
        ]
    }
    
    # 创建工作流实例
    workflow = ArchitectureDesignWorkflow()
    
    print(f"测试需求总数: {len(requirement_entries)}")
    
    try:
        # 执行工作流
        result = await workflow.execute(test_requirements, "output")
        
        print(f"\n工作流执行状态: {result['status']}")
        
        if result['status'] == 'completed':
            print("✅ 工作流执行成功")
            
            # 分析需求覆盖情况
            final_result = result.get('final_result', {})
            technical_docs = final_result.get('technical_documents', {})
            traceability_doc = technical_docs.get('requirement_traceability_document', {})
            
            print(f"\n=== 需求覆盖分析 ===")
            
            # 检查需求追踪矩阵
            traceability_matrix = traceability_doc.get('traceability_matrix', {}).get('traceability_matrix', [])
            coverage_analysis = traceability_doc.get('coverage_analysis', {})
            
            print(f"需求追踪矩阵记录数: {len(traceability_matrix)}")
            print(f"总需求数: {coverage_analysis.get('total_requirements', 0)}")
            print(f"已覆盖需求数: {coverage_analysis.get('covered_requirements', 0)}")
            print(f"覆盖率: {coverage_analysis.get('coverage_percentage', 0):.1f}%")
            
            # 详细分析每个需求的覆盖情况
            print(f"\n=== 详细需求覆盖情况 ===")
            for item in traceability_matrix:
                req_id = item.get('requirement_id', '未知')
                req_desc = item.get('requirement_description', '')
                coverage_status = item.get('coverage_status', '未知')
                related_components = item.get('related_components', [])
                
                print(f"\n需求ID: {req_id}")
                print(f"需求描述: {req_desc[:50]}...")
                print(f"覆盖状态: {coverage_status}")
                print(f"相关组件: {related_components if related_components else '无'}")
                
            # 检查架构设计
            architecture_design = final_result.get('architecture_design', {})
            print(f"\n=== 架构设计概览 ===")
            print(f"架构风格: {architecture_design.get('architecture_style', '未指定')}")
            print(f"技术栈: {list(architecture_design.get('technology_stack', {}).keys())}")
            print(f"系统组件数: {len(architecture_design.get('system_components', []))}")
            
            # 检查验证结果
            validation_result = final_result.get('validation_result', {})
            print(f"\n=== 验证结果 ===")
            print(f"总体评分: {validation_result.get('overall_score', 0)}")
            print(f"可行性等级: {validation_result.get('feasibility_level', '未评估')}")
            
            # 保存结果到文件
            timestamp = result.get('timestamp', 'unknown')
            result_file = f"output/requirement_coverage_test_{timestamp}.json"
            
            # 简化结果用于保存
            simplified_result = {
                'test_info': {
                    'total_requirements': len(requirement_entries),
                    'functional_requirements': len([r for r in requirement_entries if r.get('type') == 'FR']),
                    'non_functional_requirements': len([r for r in requirement_entries if r.get('type') == 'NFR'])
                },
                'coverage_analysis': coverage_analysis,
                'traceability_matrix': traceability_matrix,
                'architecture_overview': {
                    'architecture_style': architecture_design.get('architecture_style'),
                    'technology_stack': list(architecture_design.get('technology_stack', {}).keys()),
                    'component_count': len(architecture_design.get('system_components', [])),
                    'key_components': [comp.get('name', '未知组件') for comp in architecture_design.get('system_components', [])[:10]]
                },
                'validation_summary': {
                    'overall_score': validation_result.get('overall_score', 0),
                    'feasibility_level': validation_result.get('feasibility_level', '未评估'),
                    'key_strengths': validation_result.get('key_strengths', []),
                    'potential_risks': validation_result.get('potential_risks', [])
                }
            }
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(simplified_result, f, ensure_ascii=False, indent=2)
                
            print(f"\n✅ 测试结果已保存到: {result_file}")
            
            # 评估闭环完整性
            coverage_percentage = coverage_analysis.get('coverage_percentage', 0)
            if coverage_percentage >= 90:
                print(f"\n🎉 闭环完整性评估: 优秀 (覆盖率: {coverage_percentage:.1f}%)")
            elif coverage_percentage >= 70:
                print(f"\n✅ 闭环完整性评估: 良好 (覆盖率: {coverage_percentage:.1f}%)")
            elif coverage_percentage >= 50:
                print(f"\n⚠️  闭环完整性评估: 一般 (覆盖率: {coverage_percentage:.1f}%)")
            else:
                print(f"\n❌ 闭环完整性评估: 需要改进 (覆盖率: {coverage_percentage:.1f}%)")
                
        else:
            print(f"❌ 工作流执行失败: {result.get('error', '未知错误')}")
            
            # 检查失败详情
            for step_result in result.get('step_results', []):
                if step_result['status'] == 'failed':
                    print(f"失败步骤: {step_result['step_name']}")
                    print(f"失败原因: {step_result.get('error', '未知错误')}")
                    
    except Exception as e:
        print(f"❌ 测试执行失败: {str(e)}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_requirement_coverage())