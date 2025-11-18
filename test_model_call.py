import asyncio
import os
from config import DASHSCOPE_API_KEY

async def test_model_call():
    """测试模型调用方式"""
    
    print("测试 DashScopeChatModel 调用方式...")
    
    if not DASHSCOPE_API_KEY:
        print("未配置 DASHSCOPE_API_KEY")
        return
    
    try:
        from agentscope.model import DashScopeChatModel
        
        # 创建模型实例
        model = DashScopeChatModel(
            model_name="qwen-turbo",
            api_key=DASHSCOPE_API_KEY,
            generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
        )
        
        print("模型实例创建成功")
        
        # 测试不同的调用方式
        print("\n测试调用方式 1: await model([message])")
        try:
            response = await model([{"role": "user", "content": "Hello"}])
            print(f"响应类型: {type(response)}")
            print(f"响应内容: {response}")
            
            # 测试处理方法
            content = ""
            async for chunk in response:
                print(f"Chunk 类型: {type(chunk)}")
                print(f"Chunk 属性: {list(chunk.__dict__.keys()) if hasattr(chunk, '__dict__') else '无 __dict__'}")
                
                # 尝试不同的属性访问方式
                try:
                    if hasattr(chunk, 'text'):
                        print(f"有 text 属性")
                        text_content = chunk.text
                        content += text_content
                        print(f"Chunk text: {text_content}")
                except Exception as e:
                    print(f"访问 text 属性失败: {e}")
                    
                try:
                    if hasattr(chunk, 'content'):
                        print(f"有 content 属性")
                        content_value = chunk.content
                        print(f"Content 类型: {type(content_value)}")
                        print(f"Content 值: {content_value}")
                        
                        if isinstance(content_value, list):
                            # 如果是列表，连接所有字符串元素
                            content_str = ''.join(str(item) for item in content_value)
                            content += content_str
                            print(f"处理后的 content: {content_str}")
                        else:
                            content += str(content_value)
                            print(f"Content: {content_value}")
                except Exception as e:
                    print(f"访问 content 属性失败: {e}")
                    
                try:
                    if hasattr(chunk, 'message'):
                        print(f"有 message 属性")
                        content += str(chunk.message)
                        print(f"Chunk message: {chunk.message}")
                except Exception as e:
                    print(f"访问 message 属性失败: {e}")
                    
                if isinstance(chunk, str):
                    content += chunk
                    print(f"Chunk string: {chunk}")
            
            print(f"处理后的内容: {content}")
            
        except Exception as e:
            print(f"调用方式 1 失败: {e}")
        
        print("\n测试调用方式 2: 使用 Msg 对象")
        try:
            from agentscope.message import Msg
            msg = Msg(role="user", content="Hello")
            response = await model(msg)
            print(f"响应类型: {type(response)}")
            print(f"响应内容: {response}")
            
        except Exception as e:
            print(f"调用方式 2 失败: {e}")
            
    except ImportError as e:
        print(f"导入失败: {e}")
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_model_call())