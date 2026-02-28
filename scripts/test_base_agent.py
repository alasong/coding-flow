"""测试 BaseAgent 使用硅基流动 API"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

async def test_base_agent():
    print('=== 测试 BaseAgent 硅基流动 API ===')
    
    agent = BaseAgent(
        name="测试Agent",
        model_config_name="test"
    )
    
    print(f'模型名称: {agent.target_model_name}')
    print(f'模型对象: {agent.model}')
    
    if agent.model:
        print('\n正在调用模型...')
        response = await agent.call_llm_with_retry([
            {'role': 'user', 'content': '你好，请用一句话介绍你自己'}
        ])
        content = await agent._process_model_response(response)
        print(f'回复: {content}')
        print('\n测试成功!')
    else:
        print('模型初始化失败!')

if __name__ == '__main__':
    asyncio.run(test_base_agent())
