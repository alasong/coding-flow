"""
架构分析Agent - 负责系统架构设计和技术选型
"""

from agentscope.agent import AgentBase
from typing import Dict, List, Any
import json
import logging
from datetime import datetime
import asyncio
from config import DASHSCOPE_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class ArchitectureAnalyzerAgent(AgentBase):
    """架构分析Agent - 负责系统架构设计和技术选型"""
    
    def __init__(self, name: str, model_config_name: str):
        super().__init__()
        self.name = name
        self.model_config_name = model_config_name
        
        # 配置真实的大模型API
        if DASHSCOPE_API_KEY or OPENAI_API_KEY:
            try:
                if DASHSCOPE_API_KEY:
                    from agentscope.model import DashScopeChatModel
                    self.model = DashScopeChatModel(
                        model_name="qwen-turbo",
                        api_key=DASHSCOPE_API_KEY,
                        generate_kwargs={"temperature": 0.3, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化DashScope模型: qwen-turbo")
                else:
                    from agentscope.model import OpenAIChatModel
                    self.model = OpenAIChatModel(
                        model_name=DEFAULT_MODEL,
                        api_key=OPENAI_API_KEY,
                        generate_kwargs={"temperature": 0.3, "max_tokens": 2000}
                    )
                    logger.info(f"[{self.name}] 成功初始化OpenAI模型: {DEFAULT_MODEL}")
                    
            except Exception as e:
                logger.error(f"[{self.name}] 初始化真实模型失败: {e}")
                raise RuntimeError(f"模型初始化失败: {e}")
        else:
            logger.error(f"[{self.name}] 未配置API密钥")
            raise RuntimeError("未配置API密钥，无法初始化模型。请在环境变量中设置DASHSCOPE_API_KEY或OPENAI_API_KEY。")
    
    async def analyze_system_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析系统架构"""
        logger.info(f"[{self.name}] 开始分析系统架构")
        
        # 提取关键信息 - 优先使用需求条目
        requirement_entries = requirements.get('requirement_entries', [])
        functional_reqs = requirements.get('functional_requirements', [])
        non_functional_reqs = requirements.get('non_functional_requirements', [])
        constraints = requirements.get('constraints', [])
        
        # 构建基于需求条目的详细分析请求
        req_analysis_text = self._build_requirement_analysis_text(requirement_entries)
        
        prompt = f"""
        基于以下详细需求分析，设计完整的系统架构方案：
        
        {req_analysis_text}
        
        功能需求：
        {chr(10).join(f'- {req}' for req in functional_reqs[:15]) if functional_reqs else '暂无具体功能需求'}
        
        非功能需求：
        {chr(10).join(f'- {req}' for req in non_functional_reqs[:10]) if non_functional_reqs else '暂无具体非功能需求'}
        
        约束条件：
        {chr(10).join(f'- {constraint}' for constraint in constraints[:10]) if constraints else '暂无约束条件'}
        
        请提供详细的系统架构设计，包括：
        1. 系统架构模式（如微服务、单体、分层架构等）
        2. 技术栈选择（前端、后端、数据库、中间件）
        3. 系统组件划分和职责 - 必须覆盖所有功能需求
        4. 部署架构设计
        5. 性能考虑因素
        6. 扩展性设计方案
        7. 安全性架构考虑
        8. 监控和运维架构
        
        基于需求分析，必须包含以下核心微服务组件：
        - API Gateway: 统一入口和路由
        - User Service: 用户注册、登录、身份验证（对应FR-001, NFR-001）
        - Product Service: 商品信息管理、分类、展示（对应FR-002）
        - Search Service: 商品搜索、筛选、全文检索（对应FR-003）
        - Shopping Cart Service: 购物车管理、商品添加删除（对应FR-004）
        - Order Service: 订单创建、状态跟踪、历史查询（对应FR-005）
        - Payment Service: 支付接口集成、交易处理（对应FR-006）
        - Review Service: 用户评价、商品评分、评论管理（对应FR-007）
        - Feedback Service: 用户反馈收集、处理、回复（对应FR-008）
        - Compliance Service: 合规检查、法规遵循、审计（对应FR-009）
        - Notification Service: 消息通知、邮件、短信
        - Cache Service: Redis缓存、会话管理
        - Message Queue: Kafka/RabbitMQ异步处理
        - Monitoring Service: 系统监控、日志收集、告警
        
        请以JSON格式返回，包含以下字段：
        - architecture_pattern: 架构模式
        - technology_stack: 技术栈选择
        - system_components: 详细的系统组件列表，必须包含上述所有服务
        - deployment_architecture: 部署架构
        - performance_considerations: 性能考虑（特别针对NFR-002高并发、NFR-004响应时间）
        - scalability_design: 扩展性设计
        - security_architecture: 安全架构（特别针对NFR-003数据加密）
        - monitoring_architecture: 监控架构
        - analysis_summary: 架构分析总结，说明如何满足每个需求
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        # 解析JSON响应
        try:
            # 提取JSON内容
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                architecture_design = json.loads(json_match.group())
            else:
                # 如果无法解析JSON，创建结构化响应
                architecture_design = {
                    "architecture_pattern": "微服务架构",
                    "technology_stack": {
                        "frontend": "React/Vue.js",
                        "backend": "Spring Boot/Django",
                        "database": "MySQL/PostgreSQL",
                        "cache": "Redis",
                        "message_queue": "RabbitMQ/Apache Kafka"
                    },
                    "system_components": [
                        "用户服务", "业务服务", "数据服务", "网关服务", "监控服务"
                    ],
                    "deployment_architecture": "容器化部署，支持水平扩展",
                    "performance_considerations": "数据库优化、缓存策略、负载均衡",
                    "scalability_design": "微服务拆分，支持弹性扩展",
                    "security_architecture": "认证授权、数据加密、API安全",
                    "monitoring_architecture": "日志收集、性能监控、告警机制",
                    "analysis_summary": "基于需求分析，推荐采用微服务架构"
                }
        except Exception as e:
            logger.warning(f"解析架构设计JSON失败: {e}")
            architecture_design = {
                "architecture_pattern": "分层架构",
                "technology_stack": {"frontend": "React", "backend": "Spring Boot", "database": "MySQL"},
                "system_components": ["Web层", "业务逻辑层", "数据访问层"],
                "deployment_architecture": "传统部署模式",
                "analysis_summary": "基于需求分析设计架构"
            }
        
        return architecture_design
    
    def _build_requirement_analysis_text(self, requirement_entries: List[Dict[str, Any]]) -> str:
        """构建需求分析文本"""
        if not requirement_entries:
            return "暂无具体需求条目"
        
        fr_reqs = [req for req in requirement_entries if req.get('id', '').startswith('FR-')]
        nfr_reqs = [req for req in requirement_entries if req.get('id', '').startswith('NFR-')]
        
        analysis_text = f"需求分析总结：\n"
        analysis_text += f"总需求数：{len(requirement_entries)}\n"
        analysis_text += f"功能需求：{len(fr_reqs)}个\n"
        analysis_text += f"非功能需求：{len(nfr_reqs)}个\n\n"
        
        if fr_reqs:
            analysis_text += "功能需求详情：\n"
            for req in fr_reqs:
                analysis_text += f"- {req.get('id', '')}: {req.get('description', '')} (优先级：{req.get('priority', '中')})\n"
        
        if nfr_reqs:
            analysis_text += "\n非功能需求详情：\n"
            for req in nfr_reqs:
                analysis_text += f"- {req.get('id', '')}: {req.get('description', '')} (优先级：{req.get('priority', '中')})\n"
        
        return analysis_text
    
    async def design_database_schema(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """设计数据库架构"""
        logger.info(f"[{self.name}] 开始设计数据库架构")
        
        functional_reqs = requirements.get('functional_requirements', [])
        
        prompt = f"""
        基于以下功能需求，设计数据库架构：
        
        功能需求：
        {chr(10).join(f'- {req}' for req in functional_reqs[:15]) if functional_reqs else '暂无具体功能需求'}
        
        请提供详细的数据库设计方案，包括：
        1. 数据库类型选择（关系型/非关系型/混合）
        2. 主要数据表设计
        3. 表结构和字段定义
        4. 主键和外键关系
        5. 索引设计策略
        6. 数据分区和分表策略
        7. 数据备份和恢复策略
        8. 数据库性能优化方案
        
        请以JSON格式返回，包含以下字段：
        - database_type: 数据库类型
        - tables: 数据表列表
        - relationships: 表关系
        - indexing_strategy: 索引策略
        - optimization_strategy: 优化策略
        - backup_strategy: 备份策略
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                database_design = json.loads(json_match.group())
            else:
                database_design = self._generate_default_database_design()
        except Exception as e:
            logger.warning(f"解析数据库设计JSON失败: {e}")
            database_design = self._generate_default_database_design()
        
        return database_design
    
    async def analyze_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析架构 - 主方法"""
        logger.info(f"[{self.name}] 开始分析架构")
        
        # 并行执行三个分析任务
        system_task = self.analyze_system_architecture(requirements)
        database_task = self.design_database_schema(requirements)
        api_task = self.design_api_architecture(requirements)
        
        # 等待所有任务完成
        system_arch, database_schema, api_arch = await asyncio.gather(
            system_task, database_task, api_task
        )
        
        # 整合结果
        architecture_analysis = {
            "system_architecture": system_arch,
            "database_design": database_schema,
            "api_architecture": api_arch,
            "technology_stack": system_arch.get("technology_stack", {}),
            "analysis_summary": self._generate_architecture_summary(system_arch, database_schema, api_arch)
        }
        
        logger.info(f"[{self.name}] 架构分析完成")
        return architecture_analysis
    
    def _generate_architecture_summary(self, system_arch: Dict, database_schema: Dict, api_arch: Dict) -> str:
        """生成架构分析总结"""
        return f"""
        系统架构分析完成：
        - 架构模式：{system_arch.get('architecture_pattern', '未知')}
        - 数据库类型：{database_schema.get('database_type', '未知')}
        - API风格：{api_arch.get('api_style', '未知')}
        - 技术栈：{', '.join(system_arch.get('technology_stack', {}).keys())}
        """.strip()
    
    def _generate_default_architecture_analysis(self) -> Dict[str, Any]:
        """生成默认架构分析"""
        return {
            "system_architecture": {
                "architecture_pattern": "微服务架构",
                "technology_stack": {"frontend": "React", "backend": "Spring Boot", "database": "MySQL"},
                "analysis_summary": "默认架构分析"
            },
            "database_design": {
                "database_type": "MySQL",
                "tables": [],
                "optimization_strategy": "默认优化策略"
            },
            "api_architecture": {
                "api_style": "RESTful",
                "api_endpoints": [],
                "authentication": "JWT"
            },
            "analysis_summary": "使用默认架构分析结果"
        }
    
    def _generate_default_database_design(self) -> Dict[str, Any]:
        """生成默认数据库设计"""
        return {
            "database_type": "关系型数据库(MySQL/PostgreSQL)",
            "tables": [
                {
                    "name": "users",
                    "description": "用户表",
                    "fields": ["id", "username", "email", "created_at", "updated_at"]
                },
                {
                    "name": "business_data", 
                    "description": "业务数据表",
                    "fields": ["id", "user_id", "data", "status", "created_at"]
                }
            ],
            "relationships": "用户表与业务数据表一对多关系",
            "indexing_strategy": "基于查询需求建立索引",
            "optimization_strategy": "查询优化、存储优化",
            "backup_strategy": "定期备份、增量备份"
        }
    
    async def design_api_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """设计API架构"""
        logger.info(f"[{self.name}] 开始设计API架构")
        
        functional_reqs = requirements.get('functional_requirements', [])
        
        prompt = f"""
        基于以下功能需求，设计API架构方案：
        
        功能需求：
        {chr(10).join(f'- {req}' for req in functional_reqs[:15]) if functional_reqs else '暂无具体功能需求'}
        
        请提供详细的API设计方案，包括：
        1. API设计风格（RESTful/GraphQL/gRPC等）
        2. API端点设计
        3. 请求和响应格式
        4. 认证和授权机制
        5. 错误处理机制
        6. API版本管理策略
        7. API文档规范
        8. 性能优化策略
        
        请以JSON格式返回，包含以下字段：
        - api_style: API风格
        - api_endpoints: API端点列表
        - authentication: 认证机制
        - error_handling: 错误处理
        - versioning_strategy: 版本管理
        - performance_optimization: 性能优化
        """
        
        response = await self.model([{"role": "user", "content": prompt}])
        content = await self._process_model_response(response)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                api_design = json.loads(json_match.group())
            else:
                api_design = self._generate_default_api_design()
        except Exception as e:
            logger.warning(f"解析API设计JSON失败: {e}")
            api_design = self._generate_default_api_design()
        
        return api_design
    
    def _generate_default_api_design(self) -> Dict[str, Any]:
        """生成默认API设计"""
        return {
            "api_style": "RESTful API",
            "api_endpoints": [
                {"path": "/api/v1/users", "method": "GET", "description": "获取用户列表"},
                {"path": "/api/v1/users", "method": "POST", "description": "创建用户"}
            ],
            "authentication": "JWT Token",
            "error_handling": "统一错误码和错误信息",
            "versioning_strategy": "URL路径版本控制",
            "performance_optimization": "缓存、分页、限流"
        }
    
    async def _process_model_response(self, response):
        """处理模型响应，支持流式和非流式响应"""
        if hasattr(response, '__aiter__'):
            # 处理流式响应 - 修复重复累积问题
            content_parts = []
            last_content = ""
            
            async for chunk in response:
                current_content = ""
                
                if hasattr(chunk, 'content'):
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
                    new_content = current_content[len(last_content):]
                    if new_content:
                        content_parts.append(new_content)
                elif current_content != last_content:
                    content_parts.append(current_content)
                
                last_content = current_content
            
            return "".join(content_parts)
        elif hasattr(response, 'text'):
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