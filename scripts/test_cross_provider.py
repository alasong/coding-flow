"""测试跨平台降级功能"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, get_available_providers, _get_default_model_for_provider
from config import LLM_PROVIDER_PRIORITY

async def test_cross_provider():
    print('=== 测试跨平台降级功能 ===')
    
    # 显示可用平台
    providers = get_available_providers()
    print(f'可用平台: {providers}')
    print(f'配置优先级: {LLM_PROVIDER_PRIORITY}')
    
    for provider in providers:
        model = _get_default_model_for_provider(provider)
        print(f'  - {provider}: {model}')
    
    print('\n正在测试 BaseAgent 调用...')
    agent = BaseAgent(
        name="测试Agent",
        model_config_name="test"
    )
    
    print(f'当前平台: {agent.current_provider}')
    print(f'当前模型: {agent.target_model_name}')
    
    if agent.available_providers:
        print('\n正在调用模型...')
        response = await agent.call_llm_with_retry([
            {'role': 'user', 'content': '你好，请用一句话介绍你自己'}
        ])
        content = await agent._process_model_response(response)
        print(f'使用平台: {agent.current_provider}')
        print(f'使用模型: {agent.target_model_name}')
        print(f'回复: {content[:200]}...' if len(content) > 200 else f'回复: {content}')
        print('\n测试成功!')
    else:
        print('没有可用的 LLM 平台!')

if __name__ == '__main__':
    asyncio.run(test_cross_provider())
