#!/usr/bin/env python3
"""
软件需求分析工作流主程序
基于多智能体的需求分析系统
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入必要的模块
from config import OPENAI_API_KEY, DASHSCOPE_API_KEY, DEFAULT_MODEL, LOG_LEVEL
from workflow.requirement_workflow import RequirementAnalysisWorkflow
from utils.common import setup_logging, validate_user_input

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

def main():
    """主函数"""
    # 设置日志
    setup_logging(LOG_LEVEL)
    logger = logging.getLogger(__name__)
    
    logger.info("启动软件需求分析工作流系统")
    
    # 获取模型配置
    model_configs = get_model_config()
    
    # 创建工作流实例
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