#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能软件开发工作流主程序
集成需求分析工作流和架构设计工作流的统一入口
"""

import os
import sys
import logging
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入必要的模块
from config import OPENAI_API_KEY, DASHSCOPE_API_KEY, DEFAULT_MODEL, LOG_LEVEL
from workflow.master_workflow import MasterWorkflow
from workflow.requirement_workflow import RequirementAnalysisWorkflow
from utils.common import setup_logging, validate_user_input

logger = logging.getLogger(__name__)

def get_model_config():
    """获取模型配置"""
    try:
        # 配置模型
        model_configs = {
            "model_type": "openai",
            "model_name": DEFAULT_MODEL,
            "api_key": OPENAI_API_KEY or DASHSCOPE_API_KEY,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # 如果没有设置API密钥，使用模拟模式
        if not OPENAI_API_KEY and not DASHSCOPE_API_KEY:
            logging.warning("未设置API密钥，将使用模拟模式运行")
            model_configs["model_type"] = "mock"
        
        return model_configs
        
    except Exception as e:
        logging.error(f"配置模型失败: {e}")
        return {"model_type": "mock"}  # 降级到模拟模式

async def process_requirements_new(user_input: str, mode: str = "sequential"):
    """处理需求的新版本"""
    try:
        print(f"开始执行 {mode} 模式...")
        
        # 创建主工作流实例
        master_workflow = MasterWorkflow()
        
        # 执行工作流
        result = await master_workflow.run(user_input, workflow_mode=mode)
        
        # 显示结果摘要
        print("\n" + "="*60)
        print("工作流执行完成")
        print("="*60)
        
        workflow_info = result.get("workflow_info", {})
        print(f"执行模式: {workflow_info.get('mode', 'unknown')}")
        print(f"总耗时: {workflow_info.get('total_duration', 0):.2f} 秒")
        print(f"执行状态: {workflow_info.get('status', 'unknown')}")
        
        # 显示需求分析结果
        if "requirement_analysis" in result.get("results", {}):
            req_result = result["results"]["requirement_analysis"]
            req_info = req_result.get("workflow_info", {})
            print(f"\n需求分析:")
            print(f"  - 状态: {req_info.get('status', 'unknown')}")
            print(f"  - 耗时: {req_info.get('total_duration', 0):.2f} 秒")
            print(f"  - 核心需求: {len(req_result.get('core_requirements', {}))} 条")
        
        # 显示架构设计结果
        if "architecture_design" in result.get("results", {}):
            arch_result = result["results"]["architecture_design"]
            arch_info = arch_result.get("workflow_info", {})
            validation = arch_result.get("architecture_validation", {})
            print(f"\n架构设计:")
            print(f"  - 状态: {arch_info.get('status', 'unknown')}")
            print(f"  - 耗时: {arch_info.get('total_duration', 0):.2f} 秒")
            if validation:
                print(f"  - 总体评分: {validation.get('overall_score', 0)}/10")
        
        print(f"\n详细结果已保存到 output 目录")
        print("="*60)
        
        return result
        
    except Exception as e:
        logger.error(f"处理失败: {e}")
        print(f"\n处理失败: {e}")
        return None

class WorkflowRunner:
    """工作流运行器"""
    
    def __init__(self, mode='sequential', debug_requirements=False, debug_architecture=False, show_mapping=False, validate_coverage=False):
        self.mode = mode
        self.debug_requirements = debug_requirements
        self.debug_architecture = debug_architecture
        self.show_mapping = show_mapping
        self.validate_coverage = validate_coverage
        self.master_workflow = MasterWorkflow()
    
    async def run_interactive_mode(self):
        """交互式模式"""
        print("\n" + "="*60)
        print("智能软件开发工作流系统")
        print("="*60)
        print("\n可用工作流模式:")
        print("1. 顺序模式 - 先需求分析，后架构设计")
        print("2. 并行模式 - 同时执行需求分析和架构设计")
        print("3. 仅需求分析 - 仅执行需求分析工作流")
        print("4. 仅架构设计 - 仅执行架构设计工作流")
        print("5. 退出系统")
        
        while True:
            try:
                choice = input("\n请选择工作流模式 (1-5): ").strip()
                
                if choice == '5':
                    print("感谢使用，再见！")
                    break
                
                if choice not in ['1', '2', '3', '4']:
                    print("无效选择，请重新输入")
                    continue
                
                # 获取用户输入
                print("\n请输入项目需求描述 (输入空行结束):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "":
                        break
                    lines.append(line)
                
                if not lines:
                    print("输入不能为空")
                    continue
                
                input_text = '\n'.join(lines)
                
                # 根据选择执行相应的工作流
                if choice == '1':
                    mode = "sequential"
                    print("\n开始执行顺序模式...")
                elif choice == '2':
                    mode = "parallel"
                    print("\n开始执行并行模式...")
                elif choice == '3':
                    mode = "requirement_only"
                    print("\n开始执行需求分析...")
                elif choice == '4':
                    mode = "architecture_only"
                    print("\n开始执行架构设计...")
                
                # 执行工作流
                result = await self.master_workflow.run(input_text, workflow_mode=mode)
                
                # 显示结果摘要
                self._display_summary(result)
                
            except KeyboardInterrupt:
                print("\n\n操作被取消")
                break
            except Exception as e:
                logger.error(f"执行失败: {e}")
                print(f"\n执行失败: {e}")
                print("请检查日志文件获取详细信息")
    
    async def run_batch_mode(self, input_file: str, mode: str):
        """批量处理模式"""
        try:
            # 读取输入文件
            input_path = Path(input_file)
            if not input_path.exists():
                print(f"错误: 输入文件 {input_file} 不存在")
                return
            
            with open(input_path, 'r', encoding='utf-8') as f:
                input_text = f.read()
            
            if not input_text.strip():
                print("错误: 输入文件内容为空")
                return
            
            print(f"开始执行 {mode} 模式...")
            result = await self.master_workflow.run(input_text, workflow_mode=mode)
            
            # 显示结果摘要
            self._display_summary(
                result,
                debug_requirements=self.debug_requirements,
                debug_architecture=self.debug_architecture,
                show_mapping=self.show_mapping,
                validate_coverage=self.validate_coverage
            )
            
        except Exception as e:
            logger.error(f"批量处理失败: {e}")
            print(f"批量处理失败: {e}")
    
    def _display_summary(self, result: dict, debug_requirements=False, debug_architecture=False, show_mapping=False, validate_coverage=False):
        """显示结果摘要"""
        workflow_info = result.get("workflow_info", {})
        
        print("\n" + "="*60)
        print("工作流执行完成")
        print("="*60)
        
        print(f"执行模式: {workflow_info.get('mode', 'unknown')}")
        print(f"总耗时: {workflow_info.get('total_duration', 0):.2f} 秒")
        print(f"执行状态: {workflow_info.get('status', 'unknown')}")
        
        # 显示需求分析结果
        if "requirement_analysis" in result.get("results", {}):
            req_result = result["results"]["requirement_analysis"]
            req_info = req_result.get("workflow_info", {})
            # 回退计算状态与耗时
            status = req_info.get("status") or req_result.get("status", "completed")
            duration = req_info.get("total_duration")
            if duration is None:
                from datetime import datetime
                start = req_result.get("start_time")
                end = req_result.get("end_time")
                try:
                    if start and end:
                        duration = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
                    else:
                        duration = 0.0
                except Exception:
                    duration = 0.0
            print(f"\n需求分析:")
            print(f"  - 状态: {status}")
            print(f"  - 耗时: {duration:.2f} 秒")
            
            # 从分析结果中获取需求条目
            analysis_results = req_result.get("results", {})
            requirements_data = analysis_results.get("analysis_results", {}).get("requirements", {})
            requirement_entries = requirements_data.get("requirement_entries", [])
            print(f"  - 需求条目: {len(requirement_entries)} 条")
            
            if debug_requirements and requirement_entries:
                print(f"  - 需求条目详情:")
                for entry in requirement_entries[:5]:  # 显示前5个
                    print(f"    * {entry.get('id', 'N/A')}: {entry.get('description', 'N/A')[:50]}...")
                if len(requirement_entries) > 5:
                    print(f"    ... 还有 {len(requirement_entries) - 5} 个需求条目")
        
        # 显示架构设计结果
        if "architecture_design" in result.get("results", {}):
            arch_result = result["results"]["architecture_design"]
            arch_info = arch_result.get("workflow_info", {})
            validation = arch_result.get("architecture_validation", {})
            print(f"\n架构设计:")
            status = arch_info.get("status") or arch_result.get("status", "completed")
            duration = arch_info.get("total_duration")
            if duration is None:
                from datetime import datetime
                start = arch_result.get("start_time")
                end = arch_result.get("end_time")
                try:
                    if start and end:
                        duration = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
                    else:
                        duration = 0.0
                except Exception:
                    duration = 0.0
            print(f"  - 状态: {status}")
            print(f"  - 耗时: {duration:.2f} 秒")
            if validation:
                print(f"  - 总体评分: {validation.get('overall_score', 0)}/10")
                
                if debug_architecture:
                    components = arch_result.get("architecture_design", {}).get("components", [])
                    print(f"  - 系统组件: {len(components)} 个")
                if components:
                    print(f"    组件列表:")
                    for component in components[:5]:
                        print(f"    * {component.get('name', 'N/A')}: {component.get('description', 'N/A')[:40]}...")
                    if len(components) > 5:
                        print(f"    ... 还有 {len(components) - 5} 个组件")

        # 显示项目分解结果
        if "decomposition" in result.get("results", {}):
            decomp = result["results"]["decomposition"]
            print(f"\n项目分解:")
            print(f"  - 状态: {decomp.get('status', 'unknown')}")
            steps = decomp.get("steps", {})
            wp = steps.get("work_packages", {})
            cov = steps.get("coverage", {})
            if wp:
                print(f"  - 工作包: {wp.get('count', 0)} 个")
            if cov:
                print(f"  - 覆盖度: {cov.get('coverage_percentage', 0):.2f}%")

        # 显示项目开发结果
        if "development_execution" in result.get("results", {}):
            devexec = result["results"]["development_execution"]
            print(f"\n项目开发:")
            print(f"  - 状态: {devexec.get('status', 'unknown')}")
            final = devexec.get("final_result", {})
            scaffold = final.get("scaffold", {})
            code_dir = scaffold.get("code_dir")
            if code_dir:
                print(f"  - 代码目录: {code_dir}")
            steps = devexec.get("steps", {})
            if "frontend" in steps:
                print("  - 模式: Web 前端")
            if "cli" in steps:
                print("  - 模式: CLI")
        
        # 显示需求-架构映射
        if show_mapping and "requirement_architecture_mapping" in result.get("context", {}):
            mapping = result["context"]["requirement_architecture_mapping"]
            print(f"\n需求-架构关联映射:")
            coverage = mapping.get("overall_coverage", {})
            print(f"  - 总需求数: {coverage.get('total_requirements', 0)}")
            print(f"  - 已覆盖需求: {coverage.get('covered_requirements', 0)}")
            print(f"  - 覆盖率: {coverage.get('coverage_percentage', 0):.1f}%")
            
            if validate_coverage:
                mappings = mapping.get("mappings", [])
                if mappings:
                    covered = [m for m in mappings if m.get("coverage_status") == "已覆盖"]
                    uncovered = [m for m in mappings if m.get("coverage_status") == "未覆盖"]
                    
                    if covered:
                        print(f"  - 已覆盖的需求:")
                        for m in covered[:3]:
                            print(f"    * {m.get('requirement_id')}: {m.get('requirement_description')[:30]}... -> {m.get('related_components', [])}")
                    
                    if uncovered:
                        print(f"  - 未覆盖的需求:")
                        for m in uncovered[:3]:
                            print(f"    * {m.get('requirement_id')}: {m.get('requirement_description')[:30]}...")
                else:
                    print(f"  - 暂无映射数据")
        
        print(f"\n详细结果已保存到 output 目录")
        print("="*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能软件开发工作流系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式模式
  python main.py
  
  # 批量处理模式
  python main.py -f requirements.txt -m sequential
  python main.py -f requirements.txt -m requirement_only
  
  # 查看工作流信息
  python main.py --info
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='输入文件路径 (批量处理模式)'
    )
    
    parser.add_argument(
        '-m', '--mode',
        type=str,
        choices=['sequential', 'parallel', 'requirement_only', 'architecture_only'],
        default='sequential',
        help='工作流模式 (默认: sequential)'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='显示工作流信息并退出'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--debug-requirements',
        action='store_true',
        help='调试需求分析过程，显示详细的需求条目信息'
    )
    
    parser.add_argument(
        '--debug-architecture',
        action='store_true',
        help='调试架构设计过程，显示组件匹配详情'
    )
    
    parser.add_argument(
        '--show-mapping',
        action='store_true',
        help='显示需求与架构的关联映射结果'
    )
    
    parser.add_argument(
        '--validate-coverage',
        action='store_true',
        help='验证需求覆盖率并显示详细报告'
    )
    
    # 如果没有参数，进入交互式模式
    if len(sys.argv) == 1:
        # 传统交互式模式
        return run_interactive_mode()
    
    args = parser.parse_args()
    
    # 设置日志级别
    setup_logging(args.log_level)
    logger.info("启动智能软件开发工作流系统")
    
    # 创建工作流运行器
    runner = WorkflowRunner(
        mode=args.mode,
        debug_requirements=args.debug_requirements,
        debug_architecture=args.debug_architecture,
        show_mapping=args.show_mapping,
        validate_coverage=args.validate_coverage
    )
    
    # 显示工作流信息
    if args.info:
        info = runner.master_workflow.get_workflow_info()
        print("\n工作流系统信息:")
        print("="*60)
        print(f"系统名称: {info['name']}")
        print(f"描述: {info['description']}")
        print(f"启用状态:")
        for workflow, enabled in info['enabled_workflows'].items():
            print(f"  - {workflow}: {'启用' if enabled else '禁用'}")
        print(f"总运行次数: {info['total_runs']}")
        print("="*60)
        return
    
    # 运行工作流
    try:
        if args.file:
            # 批量处理模式
            asyncio.run(runner.run_batch_mode(args.file, args.mode))
        else:
            # 交互式模式
            asyncio.run(runner.run_interactive_mode())
    
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"程序执行失败: {e}")
        sys.exit(1)

def run_interactive_mode():
    """传统交互式模式（向后兼容）"""
    # 设置日志
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger(__name__)
    
    logger.info("启动软件需求分析工作流系统")
    
    # 创建工作流实例（向后兼容）
    workflow = RequirementAnalysisWorkflow()
    
    # 示例用户输入
    sample_inputs = [
        "我们需要开发一个在线购物系统，用户可以浏览商品、添加到购物车、下订单和支付。系统需要支持多种支付方式，包括支付宝、微信支付和银行卡。还需要有管理员后台，可以管理商品、订单和用户信息。",
        "请帮我分析一个员工管理系统的需求，包括员工信息管理、考勤管理、薪资计算、绩效评估等功能。",
        "我想开发一个智能客服系统，能够自动回答用户问题，支持多渠道接入，包括网页、微信、电话等。"
    ]
    
    print("=" * 60)
    print("软件需求分析工作流系统")
    print("=" * 60)
    print("请选择输入方式：")
    print("1. 使用示例需求")
    print("2. 自定义输入需求")
    print("3. 查看工作流状态")
    print("4. 退出")
    print("-" * 60)
    
    while True:
        try:
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == "1":
                # 使用示例输入
                print("\n可用示例需求：")
                for i, example in enumerate(sample_inputs, 1):
                    print(f"{i}. {example[:100]}...")
                
                example_choice = input("\n选择示例 (1-3): ").strip()
                if example_choice.isdigit() and 1 <= int(example_choice) <= 3:
                    user_input = sample_inputs[int(example_choice) - 1]
                    asyncio.run(process_requirements(workflow, user_input))
                else:
                    print("无效选择，请重试")
                    
            elif choice == "2":
                # 自定义输入
                print("\n请输入您的软件需求描述：")
                print("提示：请尽可能详细描述您的需求，包括功能、性能、用户角色等")
                print("-" * 40)
                user_input = input("需求描述: ").strip()
                
                if validate_user_input(user_input):
                    asyncio.run(process_requirements(workflow, user_input))
                else:
                    print("输入太短或不够具体，请提供更详细的需求描述")
                    
            elif choice == "3":
                # 查看状态
                status = workflow.get_workflow_status()
                print("\n工作流状态：")
                print(f"已初始化Agent数量: {status['agents_initialized']}")
                print(f"Agent状态: {status['agents_status']}")
                print(f"工作流数据大小: {status['workflow_data_size']} 字节")
                
            elif choice == "4":
                print("感谢使用，再见！")
                break
                
            else:
                print("无效选项，请重新选择")
                
        except KeyboardInterrupt:
            print("\n\n程序被中断，正在退出...")
            break
        except Exception as e:
            logger.error(f"发生错误: {e}")
            print(f"发生错误: {e}")
            print("请重试或联系技术支持")

async def process_requirements(workflow: RequirementAnalysisWorkflow, user_input: str):
    """处理需求分析"""
    print("\n" + "=" * 60)
    print("开始需求分析工作流...")
    print("=" * 60)
    
    try:
        # 运行工作流
        result = await workflow.run(user_input)
        
        # 显示结果摘要
        print("\n需求分析完成！")
        print("-" * 60)
        print(f"状态: {result['status']}")
        if result['status'] == 'success':
            print(f"输出文件: {result['output_file']}")
        else:
            print(f"错误: {result['error']}")
        print("-" * 60)
        
    except Exception as e:
        logging.error(f"需求分析失败: {e}")
        print(f"需求分析失败: {e}")
        print("请检查输入和配置，然后重试")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被中断，正在退出...")
        sys.exit(0)
