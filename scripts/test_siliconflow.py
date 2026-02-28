"""测试硅基流动 API 连接"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL, SILICONFLOW_DEFAULT_MODEL

print('=== 硅基流动 API 测试 ===')
print(f'API Key: {SILICONFLOW_API_KEY[:15]}...' if SILICONFLOW_API_KEY else '未配置')
print(f'Base URL: {SILICONFLOW_BASE_URL}')
print(f'Default Model: {SILICONFLOW_DEFAULT_MODEL}')

async def test_api():
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(
        api_key=SILICONFLOW_API_KEY,
        base_url=SILICONFLOW_BASE_URL
    )
    
    print('\n正在调用 API...')
    response = await client.chat.completions.create(
        model=SILICONFLOW_DEFAULT_MODEL,
        messages=[{'role': 'user', 'content': '你好，请用一句话介绍你自己'}],
        max_tokens=100
    )
    
    print(f'\n模型: {response.model}')
    print(f'回复: {response.choices[0].message.content}')
    print('\n测试成功!')

if __name__ == '__main__':
    asyncio.run(test_api())
