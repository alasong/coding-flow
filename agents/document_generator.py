from agentscope.agent import AgentBase
from agentscope.message import Msg
from typing import Dict, List, Any
import json
import logging
from datetime import datetime
import os
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class DocumentGeneratorAgent(AgentBase):
    """文档生成Agent - 生成需求规格说明书"""
    
    def __init__(self, name: str, model_config_name: str):
        super().__init__()
        self.name = name
        self.model_config_name = model_config_name
        
        # 配置真实的大模型API
        if DASHSCOPE_API_KEY or OPENAI_API_KEY:
            try:
                # 根据API密钥类型选择模型
                if DASHSCOPE_API_KEY:
                    from agentscope.model import DashScopeChatModel
                    self.model = DashScopeChatModel(
                        model_name="qwen-turbo",
                        api_key=DASHSCOPE_API_KEY,
                        generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化DashScope模型: qwen-turbo")
                else:
                    from agentscope.model import OpenAIChatModel
                    self.model = OpenAIChatModel(
                        model_name=DEFAULT_MODEL,
                        api_key=OPENAI_API_KEY,
                        generate_kwargs={"temperature": 0.7, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化OpenAI模型: {DEFAULT_MODEL}")
                
            except Exception as e:
                logger.error(f"[{self.name}] 初始化真实模型失败: {e}")
                raise RuntimeError(f"模型初始化失败: {e}")
        else:
            logger.error(f"[{self.name}] 未配置API密钥")
            raise RuntimeError("未配置API密钥，无法初始化模型。请在环境变量中设置DASHSCOPE_API_KEY或OPENAI_API_KEY。")
    
    async def generate_requirement_specification(self, requirements: Dict[str, Any]) -> str:
        """生成需求规格说明书"""
        prompt = f"""
        请基于以下需求生成一份专业的需求规格说明书：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        需求规格说明书应包含以下部分：
        1. 引言
           - 目的
           - 范围
           - 定义、缩写和术语
           - 参考资料
        2. 总体描述
           - 产品视角
           - 产品功能
           - 用户特征
           - 约束条件
           - 假设和依赖关系
        3. 具体需求
           - 功能需求
           - 非功能需求
           - 接口需求
           - 性能需求
           - 安全需求
           - 其他需求
        4. 附录
        
        请使用专业的技术文档格式，确保内容完整、清晰、无歧义。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return content
    
    async def generate_test_plan(self, requirements: Dict[str, Any]) -> str:
        """生成测试计划"""
        prompt = f"""
        请基于以下需求生成一份详细的测试计划：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        测试计划应包含：
        1. 测试目标
        2. 测试范围
        3. 测试策略
           - 功能测试
           - 性能测试
           - 安全测试
           - 兼容性测试
           - 用户接受测试
        4. 测试环境
        5. 测试用例设计
        6. 测试进度安排
        7. 测试资源
        8. 风险评估
        9. 测试完成标准
        
        请确保测试计划全面且可执行。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return content
    
    async def generate_user_manual(self, requirements: Dict[str, Any]) -> str:
        """生成用户手册"""
        prompt = f"""
        请基于以下需求生成一份用户手册：
        
        {json.dumps(requirements, ensure_ascii=False, indent=2)}
        
        用户手册应包含：
        1. 产品概述
        2. 系统要求
        3. 安装指南
        4. 功能使用说明
        5. 操作步骤
        6. 常见问题解答
        7. 技术支持联系方式
        
        请使用通俗易懂的语言，适合最终用户阅读。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return content
    
    async def _process_model_response(self, response):
        """处理模型响应，支持流式和非流式响应"""
        if hasattr(response, '__aiter__'):
            # 处理流式响应 - 修复重复累积问题
            content_parts = []
            last_content = ""
            
            async for chunk in response:
                current_content = ""
                
                if hasattr(chunk, 'content'):
                    # 处理 ChatResponse 对象，content 可能是列表
                    content_value = chunk.content
                    if isinstance(content_value, list):
                        for item in content_value:
                            if isinstance(item, dict) and 'text' in item:
                                current_content += item['text']
                            else:
                                current_content += str(item)
                    else:
                        current_content = str(content_value)
                elif hasattr(chunk, 'text'):
                    current_content = chunk.text
                elif isinstance(chunk, str):
                    current_content = chunk
                else:
                    current_content = str(chunk)
                
                # 检查是否是增量内容，避免重复累积
                if current_content.startswith(last_content):
                    # 如果是之前内容的扩展，只取新增部分
                    new_content = current_content[len(last_content):]
                    if new_content:
                        content_parts.append(new_content)
                elif current_content != last_content:
                    # 如果是新内容，直接添加
                    content_parts.append(current_content)
                
                last_content = current_content
            
            # 合并所有增量部分
            return "".join(content_parts)
        elif hasattr(response, 'text'):
            # 处理非流式响应
            return response.text
        elif hasattr(response, '__dict__'):
            # 如果是SimpleNamespace或其他对象，优先使用text属性或转换为dict获取text
            if 'text' in response.__dict__:
                return response.__dict__['text']
            else:
                # 如果没有text属性，返回对象的字符串表示
                return str(response)
        else:
            # 如果response没有__dict__属性，尝试其他方法
            if hasattr(response, 'text'):
                return response.text
            else:
                return str(response)
    
    async def generate_technical_documentation(self, requirements: Dict[str, Any]) -> str:
        """生成技术文档"""
        logger.info(f"[{self.name}] 开始生成技术文档")
        
        prompt = f"""
        基于以下需求，生成详细的技术文档：
        
        功能需求：{requirements.get('functional_requirements', [])}
        非功能需求：{requirements.get('non_functional_requirements', [])}
        约束条件：{requirements.get('constraints', [])}
        
        请生成包含以下内容的完整技术文档：
        1. 系统架构设计
        2. 技术栈选择
        3. 数据库设计
        4. API接口设计
        5. 部署方案
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return content
    
    async def generate_requirement_document(self, analysis_results: Dict[str, Any]) -> str:
        """生成需求文档"""
        logger.info(f"[{self.name}] 开始生成需求文档")
        
        # 提取关键信息，避免传递整个字典
        user_input = analysis_results.get('user_input', '未知项目')
        collected_req = analysis_results.get('collected_requirements', {})
        analysis_res = analysis_results.get('analysis_results', {})
        validation_res = analysis_results.get('validation_results', {})
        
        # 只提取文本描述，避免序列化整个对象
        functional_reqs = collected_req.get('functional_requirements', [])
        non_functional_reqs = collected_req.get('non_functional_requirements', [])
        key_features = collected_req.get('key_features', [])
        
        prompt = f"""
        基于以下需求分析结果，生成完整的需求规格说明书：
        
        用户输入：{user_input}
        
        功能需求：
        {chr(10).join(f'- {req}' for req in functional_reqs[:10]) if functional_reqs else '暂无具体功能需求'}
        
        非功能需求：
        {chr(10).join(f'- {req}' for req in non_functional_reqs[:10]) if non_functional_reqs else '暂无具体非功能需求'}
        
        关键功能点：
        {chr(10).join(f'- {feature}' for feature in key_features[:10]) if key_features else '暂无关键功能点'}
        
        可行性分析结果：{analysis_res.get('feasibility', '可行性分析完成') if isinstance(analysis_res, dict) else str(analysis_res)}
        
        验证结果：{validation_res.get('validation_summary', '需求验证完成') if isinstance(validation_res, dict) else str(validation_res)}
        
        请生成包含以下内容的完整需求文档：
        1. 引言和项目背景
        2. 功能需求详细描述
        3. 非功能需求详细描述
        4. 系统约束和假设
        5. 验收标准和测试要求
        6. 项目交付物和里程碑
        
        注意：请基于上述关键信息生成专业、完整的需求规格说明书。
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return content
    
    async def generate_user_stories(self, requirements: Dict[str, Any]) -> str:
        """生成用户故事"""
        logger.info(f"[{self.name}] 开始生成用户故事")
        
        prompt = f"""
        基于以下需求，生成详细的用户故事：
        
        功能需求：{requirements.get('functional_requirements', [])}
        非功能需求：{requirements.get('non_functional_requirements', [])}
        约束条件：{requirements.get('constraints', [])}
        
        请生成包含以下内容的用户故事：
        1. 用户角色和场景描述
        2. 具体的用户故事（采用"作为...我想要...以便..."格式）
        3. 验收标准
        4. 优先级划分
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return content
    
    async def generate_use_case_specification(self, requirements: Dict[str, Any]) -> str:
        """生成用例规格说明"""
        logger.info(f"[{self.name}] 开始生成用例规格说明")
        
        prompt = f"""
        基于以下需求，生成详细的用例规格说明：
        
        功能需求：{requirements.get('functional_requirements', [])}
        非功能需求：{requirements.get('non_functional_requirements', [])}
        约束条件：{requirements.get('constraints', [])}
        
        请生成包含以下内容的用例规格说明：
        1. 主要参与者（Actor）
        2. 用例图和用例列表
        3. 每个用例的详细描述（前置条件、后置条件、主流程、异常流程）
        4. 业务规则和约束
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        return content
    
    def save_document(self, content: str, filename: str, output_dir: str = "./output") -> str:
        """保存文档到文件"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.md"
        filepath = os.path.join(output_dir, full_filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"文档已保存到: {filepath}")
        return filepath