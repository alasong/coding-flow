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
                
                # 执行工作流，开启交互模式
                result = await self.master_workflow.run(input_text, workflow_mode=mode, interactive=True)
                
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
            # 批量模式默认非交互
            result = await self.master_workflow.run(input_text, workflow_mode=mode, interactive=False)
            
            # 显示结果摘要
            self._display_summary(result)
            
        except Exception as e:
            logger.error(f"批量处理失败: {e}")
            print(f"批量处理失败: {e}")

    def _display_summary(self, result: Dict[str, Any]):
        """显示执行结果摘要"""
        if not result:
            return

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
            req_info = req_result.get("workflow_info", {}) if isinstance(req_result, dict) else {}
            print(f"\n需求分析:")
            # 处理可能的字典嵌套
            if isinstance(req_result, dict):
                print(f"  - 状态: {req_info.get('status', 'unknown')}")
                print(f"  - 耗时: {req_info.get('total_duration', 0):.2f} 秒")
                core_reqs = req_result.get("core_requirements", {})
                if isinstance(core_reqs, list):
                    print(f"  - 核心需求: {len(core_reqs)} 条")
                elif isinstance(core_reqs, dict):
                    print(f"  - 核心需求: {len(core_reqs)} 条")
                
                # 显示生成的评审要点
                review_points = req_result.get("review_points", [])
                if review_points:
                    print(f"  - 评审要点: {len(review_points)} 个")
        
        # 显示架构设计结果
        if "architecture_design" in result.get("results", {}):
            arch_result = result["results"]["architecture_design"]
            # 处理可能的字典嵌套
            if isinstance(arch_result, dict):
                arch_info = arch_result.get("workflow_info", {})
                validation = arch_result.get("architecture_validation", {})
                print(f"\n架构设计:")
                print(f"  - 状态: {arch_info.get('status', 'unknown')}")
                # 尝试获取持续时间
                duration = arch_info.get("total_duration", 0)
                print(f"  - 耗时: {duration:.2f} 秒")
        
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

if __name__ == "__main__":
    main()
