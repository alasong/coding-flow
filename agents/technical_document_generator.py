import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
from config import AGENT_CONFIGS, DASHSCOPE_API_KEY, OPENAI_API_KEY, SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL, SILICONFLOW_DEFAULT_MODEL, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class BaseModel:
    """基础模型接口"""
    def __call__(self, prompt: str):
        raise NotImplementedError

class TechnicalDocumentGeneratorAgent:
    """技术文档生成Agent - 生成架构设计相关的技术文档"""
    
    def __init__(self, name: str = "技术文档生成器", model_config_name: str = "technical_document_generator", model: Optional[BaseModel] = None):
        self.name = name
        self.model_config_name = model_config_name
        self.model = model or self._get_default_model()
        self.system_prompt = AGENT_CONFIGS["technical_document_generator"]["system_prompt"]
        logger.info(f"初始化 {self.name}")
        
    def _get_default_model(self):
        """获取默认模型 - 优先使用真实API"""
        # 配置真实的大模型API
        if SILICONFLOW_API_KEY or DASHSCOPE_API_KEY or OPENAI_API_KEY:
            try:
                # 优先使用硅基流动
                if SILICONFLOW_API_KEY:
                    import os
                    from agentscope.model import OpenAIChatModel
                    original_base_url = os.environ.get("OPENAI_BASE_URL")
                    os.environ["OPENAI_BASE_URL"] = SILICONFLOW_BASE_URL
                    try:
                        model = OpenAIChatModel(
                            model_name=SILICONFLOW_DEFAULT_MODEL,
                            api_key=SILICONFLOW_API_KEY,
                            generate_kwargs={"temperature": 0.3, "max_tokens": 6000}
                        )
                        logger.info(f"[{self.name}] 成功初始化硅基流动模型: {SILICONFLOW_DEFAULT_MODEL}")
                        return model
                    finally:
                        if original_base_url:
                            os.environ["OPENAI_BASE_URL"] = original_base_url
                        else:
                            os.environ.pop("OPENAI_BASE_URL", None)
                # 根据API密钥类型选择模型
                elif DASHSCOPE_API_KEY:
                    from agentscope.model import DashScopeChatModel
                    model = DashScopeChatModel(
                        model_name="qwen-turbo",
                        api_key=DASHSCOPE_API_KEY,
                        generate_kwargs={"temperature": 0.3, "max_tokens": 6000}
                    )
                    logger.info(f"[{self.name}] 成功初始化DashScope模型: qwen-turbo")
                    return model
                else:
                    from agentscope.model import OpenAIChatModel
                    model = OpenAIChatModel(
                        model_name=DEFAULT_MODEL,
                        api_key=OPENAI_API_KEY,
                        generate_kwargs={"temperature": 0.3, "max_tokens": 4096}
                    )
                    logger.info(f"[{self.name}] 成功初始化OpenAI模型: {DEFAULT_MODEL}")
                    return model
                    
            except Exception as e:
                logger.error(f"[{self.name}] 初始化真实模型失败: {e}")
                raise RuntimeError(f"模型初始化失败: {e}")
        else:
            logger.warning(f"[{self.name}] 未配置API密钥，使用离线文档生成（回退内容）")
            return None
    
    async def generate_technical_documents(self, requirements: Dict[str, Any], architecture_design: Dict[str, Any], 
                                     validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成架构设计文档"""
        logger.info("开始生成架构设计文档")
        
        try:
            # 生成架构设计文档
            doc_content = await self._generate_architecture_design_content(requirements, architecture_design, validation_result)
            
            # 生成技术选型文档
            tech_selection_content = await self._generate_tech_selection_content(requirements, architecture_design)
            
            # 生成部署文档
            deployment_content = await self._generate_deployment_content(requirements, architecture_design, validation_result)
            
            # 生成完整的技术文档包
            technical_docs = {
                "architecture_design": doc_content,
                "technology_selection": tech_selection_content,
                "deployment_guide": deployment_content,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
            logger.info("技术文档生成完成")
            return technical_docs
            
        except Exception as e:
            logger.error(f"技术文档生成失败: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_architecture_design_content(self, requirements: Dict[str, Any], 
                                            architecture_design: Dict[str, Any], 
                                            validation_result: Dict[str, Any]) -> str:
        """生成架构设计文档内容"""
        
        prompt = f"""
{self.system_prompt}

请基于以下信息生成一份完整的架构设计文档：

## 需求规格
{json.dumps(requirements, ensure_ascii=False, indent=2)}

## 架构设计
{json.dumps(architecture_design, ensure_ascii=False, indent=2)}

## 验证结果
{json.dumps(validation_result, ensure_ascii=False, indent=2)}

## 文档要求
请生成一份专业的架构设计文档，包含以下章节：

1. **文档信息**
   - 文档标题：系统架构设计说明书
   - 版本号：v1.0
   - 创建日期：{datetime.now().strftime('%Y-%m-%d')}
   - 作者：{self.name}

2. **执行摘要**
   - 项目背景和目标
   - 架构设计概述
   - 关键技术决策
   - 主要风险和建议

3. **架构概览**
   - 系统整体架构图
   - 架构风格和设计原则
   - 核心组件和交互关系
   - 数据流和控制流

4. **技术架构**
   - 前端架构设计
   - 后端架构设计
   - 数据库架构设计
   - 缓存架构设计
   - 消息队列架构

5. **部署架构**
   - 基础设施架构
   - 网络拓扑设计
   - 容器化策略
   - 负载均衡设计
   - 高可用性设计

6. **安全架构**
   - 安全架构原则
   - 身份认证设计
   - 访问控制机制
   - 数据加密策略
   - 安全监控方案

7. **性能设计**
   - 性能指标定义
   - 性能优化策略
   - 扩展性设计
   - 负载测试方案

8. **运维架构**
   - 监控告警设计
   - 日志管理策略
   - 故障处理机制
   - 备份恢复方案
   - 变更管理流程

9. **实施计划**
   - 开发阶段划分
   - 里程碑定义
   - 资源需求评估
   - 风险缓解措施

10. **附录**
    - 术语表
    - 参考文档
    - 架构决策记录

请确保文档内容：
- 专业性和技术深度
- 实用性和可操作性
- 完整性和一致性
- 符合行业标准

文档格式要求：
- 使用Markdown格式
- 包含必要的图表和表格
- 清晰的章节结构
- 专业的技术语言
"""

        try:
            response = await self._call_model_with_streaming(prompt)
            return self._format_architecture_document(response)
        except Exception as e:
            logger.error(f"架构设计文档生成失败: {e}")
            return self._generate_fallback_architecture_content(requirements, architecture_design)
    
    async def _generate_tech_selection_content(self, requirements: Dict[str, Any], architecture_design: Dict[str, Any]) -> str:
        """生成技术选型文档内容"""
        
        prompt = f"""
{self.system_prompt}

请基于以下信息生成一份技术选型说明书：

## 需求规格
{json.dumps(requirements, ensure_ascii=False, indent=2)}

## 架构设计
{json.dumps(architecture_design, ensure_ascii=False, indent=2)}

## 文档要求
生成技术选型说明书，包含：

1. **技术选型概述**
   - 选型原则和标准
   - 评估方法论
   - 决策框架

2. **前端技术栈**
   - 框架选择
   - UI组件库
   - 状态管理方案
   - 构建工具
   - 测试框架

3. **后端技术栈**
   - 编程语言选择
   - Web框架选择
   - API设计规范
   - 微服务架构
   - 依赖注入框架

4. **数据库技术**
   - 关系型数据库选择
   - NoSQL数据库选择
   - 缓存数据库选择
   - 数据库设计工具

5. **中间件技术**
   - 消息队列选型
   - 搜索引擎选型
   - 日志收集方案
   - 监控告警工具

6. **部署和运维**
   - 容器化技术
   - 编排平台选择
   - CI/CD工具
   - 云服务提供商
   - 监控工具栈

7. **开发工具**
   - 版本控制系统
   - IDE和编辑器
   - 代码质量工具
   - 文档生成工具

8. **选型决策记录**
   - 每个技术选择的理由
   - 备选方案对比
   - 风险评估
   - 学习成本分析

请提供详细的技术对比表格和决策依据。
"""

        try:
            response = await self._call_model_with_streaming(prompt)
            return self._format_technology_selection(response)
        except Exception as e:
            logger.error(f"技术选型文档生成失败: {e}")
            return self._generate_fallback_tech_content(requirements, architecture_design)
    
    async def _generate_deployment_content(self, requirements: Dict[str, Any], 
                                   architecture_design: Dict[str, Any], 
                                   validation_result: Dict[str, Any]) -> str:
        """生成部署文档内容"""
        try:
            project_name = requirements.get("project_name", "MyProject")
            tech_stack = architecture_design.get("technology_stack", {})
            deployment_info = architecture_design.get("deployment_architecture", {})
            
            # 提取验证结果中的部署建议
            validation_data = validation_result.get("validation_result", {})
            deployment_suggestions = validation_data.get("suggestions", [])
            
            # 过滤部署相关的建议
            deployment_tips = []
            for suggestion in deployment_suggestions:
                if any(keyword in suggestion.lower() for keyword in ['deploy', 'operation', 'monitor', 'security']):
                    deployment_tips.append(suggestion)
            
            prompt = f"""
            基于以下项目信息，生成一份详细的系统部署指南文档：
            
            项目名称: {project_name}
            技术栈: {json.dumps(tech_stack, ensure_ascii=False, indent=2)}
            部署架构: {json.dumps(deployment_info, ensure_ascii=False, indent=2)}
            部署建议: {deployment_tips}
            
            请生成包含以下内容的部署指南：
            1. 部署概述
            2. 系统环境要求
            3. 基础环境准备
            4. 应用程序部署
            5. 数据库部署
            6. 监控和日志系统
            7. 安全配置
            8. 备份和恢复
            9. 运维管理
            10. 部署验证
            
            要求：
            - 提供具体的命令示例和配置文件
            - 包含详细的步骤说明
            - 提供故障排查指南
            - 包含性能优化建议
            - 提供安全最佳实践
            """
            
            # 使用流式调用获取响应
            response_content = ""
            try:
                # 调用模型获取异步迭代器
                response_stream = await self.model([{"role": "user", "content": prompt}])
                
                # 迭代流式响应
                async for chunk in response_stream:
                    if hasattr(chunk, 'content') and chunk.content:
                        # 处理content属性（可能是列表）
                        content = chunk.content
                        if isinstance(content, list) and len(content) > 0:
                            for item in content:
                                if isinstance(item, dict) and 'text' in item:
                                    response_content += item['text']
                                elif hasattr(item, 'text'):
                                    response_content += item.text
                        elif isinstance(content, str):
                            response_content += content
                    elif hasattr(chunk, 'text') and chunk.text:
                        response_content += chunk.text
                    elif hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                        response_content += chunk.message.content
            except Exception as e:
                logger.error(f"流式响应处理失败: {e}")
                return self._generate_fallback_deployment_content(requirements, architecture_design, validation_result)
            
            return self._format_deployment_guide(response_content.strip())
            
        except Exception as e:
            logger.error(f"部署文档生成失败: {e}")
            return self._generate_fallback_deployment_content(requirements, architecture_design, validation_result)

    def _infer_tech_stack_from_requirements(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """根据需求推断可能的技术栈（用于Fallback）"""
        req_text = json.dumps(requirements, ensure_ascii=False).lower()
        
        stack = {
            "frontend": "Modern Web Framework (e.g., React/Vue/Angular)",
            "backend": "High Performance Backend (e.g., Python/Go/Java/Node.js)",
            "database": "Relational Database (e.g., PostgreSQL/MySQL)",
            "cache": "Distributed Cache (e.g., Redis)",
            "message_queue": "Message Queue (e.g., RabbitMQ/Kafka)",
            "deployment": "Container Orchestration (e.g., Kubernetes)",
            "container": "Docker"
        }
        
        # 简单的启发式规则，仅用于Fallback时的基本填充，不应作为主要逻辑
        if "mobile" in req_text or "app" in req_text or "android" in req_text or "ios" in req_text:
            stack["frontend"] = "Mobile Framework (Flutter/React Native/Native)"
        elif "dashboard" in req_text or "admin" in req_text or "management" in req_text:
            stack["frontend"] = "Admin Dashboard Framework"
            
        if "data analysis" in req_text or "ai" in req_text or "machine learning" in req_text:
            stack["backend"] = "Python (FastAPI/Django) or similar data-friendly stack"
            stack["database"] = "PostgreSQL + Vector DB / OLAP DB"
        elif "enterprise" in req_text or "finance" in req_text:
            stack["backend"] = "Enterprise Grade Backend (Java/C#)"
        elif "high concurrency" in req_text or "real-time" in req_text:
            stack["backend"] = "High Concurrency Backend (Go/Rust/Java)"
            
        return stack

    def _generate_fallback_architecture_content(self, requirements: Dict[str, Any], 
                                              architecture_design: Dict[str, Any]) -> str:
        """生成架构设计文档的备用内容"""
        try:
            logger.info("生成架构设计文档备用内容")
            
            # 提取或推断架构信息
            components = architecture_design.get("components", [])
            provided_stack = architecture_design.get("technology_stack", {})
            inferred_stack = self._infer_tech_stack_from_requirements(requirements)
            
            # 合并技术栈，优先使用提供的
            tech_stack = {**inferred_stack, **provided_stack}
            
            project_name = requirements.get("project_name", "Project")
            
            doc_content = f"""# 系统架构设计说明书

## 1. 执行摘要

### 项目背景
基于用户需求分析，为 {project_name} 设计一套现代化的软件系统架构。

### 架构概述
系统采用分层架构设计，包含前端展示层、业务逻辑层、数据访问层和基础设施层。

### 关键技术决策
- 前端框架: {tech_stack.get('frontend')}
- 后端框架: {tech_stack.get('backend')}
- 数据库: {tech_stack.get('database')}
- 部署平台: {tech_stack.get('deployment')}

## 2. 架构概览

### 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │   Application   │    │      Data       │
│      Layer      │────│      Layer      │────│      Layer      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件
"""
            
            # 添加组件信息
            if components:
                for component in components:
                    doc_content += f"""
#### {component.get('name', 'Component')}
- 类型: {component.get('type', 'Module')}
- 技术栈: {component.get('technology', 'TBD')}
- 职责: {component.get('description', 'Responsible for specific business logic')}
"""
            else:
                doc_content += "\\n根据需求分析，系统将包含核心业务处理模块、用户管理模块及数据存储模块。\\n"
            
            doc_content += f"""

## 3. 技术架构

### 前端架构
- 框架选择: {tech_stack.get('frontend')}
- 交互设计: 响应式设计，支持多端适配

### 后端架构  
- 框架选择: {tech_stack.get('backend')}
- API设计: RESTful / GraphQL
- 认证授权: 基于Token的认证机制 (JWT/OAuth2)
- 消息队列: {tech_stack.get('message_queue')}

### 数据库架构
- 主数据库: {tech_stack.get('database')}
- 缓存策略: {tech_stack.get('cache')} 为热点数据提供加速

## 4. 部署架构

### 基础设施
- 容器平台: {tech_stack.get('container')}
- 编排系统: {tech_stack.get('deployment')}

## 5. 安全架构

### 安全原则
- 最小权限原则
- 数据加密存储与传输
- 输入验证与防注入

## 6. 实施计划

建议采用敏捷开发模式，分阶段迭代交付。
1. 核心原型验证
2. 基础功能开发
3. 系统集成与测试
4. 部署上线

---

**创建日期**: {datetime.now().strftime('%Y-%m-%d')}
**版本**: v1.0
**作者**: {self.name}
"""
            
            return doc_content
            
        except Exception as e:
            logger.error(f"架构设计备用内容生成失败: {e}")
            return f"# 架构设计文档\\n\\n由于生成过程中出现错误，这里提供简化的架构设计文档。\\n\\n**错误信息**: {str(e)}\\n\\n**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def _generate_fallback_tech_content(self, requirements: Dict[str, Any], 
                                     architecture_design: Dict[str, Any]) -> str:
        """生成技术选型文档的备用内容"""
        try:
            logger.info("生成技术选型备用内容")
            
            provided_stack = architecture_design.get("technology_stack", {})
            inferred_stack = self._infer_tech_stack_from_requirements(requirements)
            tech_stack = {**inferred_stack, **provided_stack}
            
            return f"""# 技术选型说明书

## 1. 技术选型概述

### 选型原则
- 成熟稳定: 选择经过验证的成熟技术
- 社区活跃: 拥有活跃的开发者社区
- 学习成本: 团队技术栈匹配度高
- 性能要求: 满足系统性能需求

## 2. 前端技术栈

### 框架选择: {tech_stack.get('frontend')}
**选择理由:**
- 符合当前主流开发模式
- 生态系统完善，组件库丰富
- 开发效率高

## 3. 后端技术栈

### 框架选择: {tech_stack.get('backend')}
**选择理由:**
- 性能优异，扩展性强
- 适合业务场景需求
- 社区支持良好

### 数据库: {tech_stack.get('database')}
**选择理由:**
- 数据一致性保证
- 支持复杂查询
- 可靠性高

### 消息队列: {tech_stack.get('message_queue')}
**选择理由:**
- 解耦系统组件
- 削峰填谷
- 异步处理

## 4. 基础设施

### 容器化与编排: {tech_stack.get('container')} / {tech_stack.get('deployment')}
**选择理由:**
- 标准化交付
- 自动化运维
- 弹性伸缩

## 5. 风险评估

### 技术风险
- 新技术引入的学习曲线
- 第三方组件的依赖风险

### 缓解措施
- 开展技术预研和POC验证
- 建立完善的监控告警体系

---

**创建日期**: {datetime.now().strftime('%Y-%m-%d')}
**版本**: v1.0
**作者**: AI架构设计助手
"""
            
        except Exception as e:
            logger.error(f"技术选型备用内容生成失败: {e}")
            return f"# 技术选型说明书\\n\\n由于生成过程中出现错误，这里提供简化的技术选型文档。\\n\\n**错误信息**: {str(e)}\\n\\n**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def _generate_fallback_deployment_content(self, requirements: Dict[str, Any], 
                                        architecture_design: Dict[str, Any], 
                                        validation_result: Dict[str, Any]) -> str:
        """生成部署文档的备用内容"""
        try:
            logger.info("生成部署文档备用内容")
            
            provided_stack = architecture_design.get("technology_stack", {})
            inferred_stack = self._infer_tech_stack_from_requirements(requirements)
            tech_stack = {**inferred_stack, **provided_stack}
            
            validation_data = validation_result.get("validation_result", {})
            deployment_suggestions = validation_data.get("suggestions", [])
            
            deployment_tips = [s for s in deployment_suggestions if any(k in s.lower() for k in ['deploy', 'operation', 'monitor', 'security'])]
            tips_content = "\\n".join([f"- {tip}" for tip in deployment_tips]) if deployment_tips else "- 建议在生产环境部署前，先在测试环境进行完整验证"

            return f"""# 系统部署指南

## 1. 部署概述

### 部署目标
确保系统能够安全、稳定地部署到 {tech_stack.get('deployment')} 环境中。

### 技术栈
- 容器化: {tech_stack.get('container')}
- 编排: {tech_stack.get('deployment')}
- 数据库: {tech_stack.get('database')}

## 2. 环境准备

### 硬件要求
根据系统规模预估：
- 开发环境: 最小配置 (e.g., 2CPU/4GB)
- 生产环境: 根据压测结果动态调整 (e.g., 4CPU/8GB 起步)

### 软件要求
- 操作系统: Linux (Ubuntu/CentOS)
- 运行时: {tech_stack.get('container')} Runtime
- 数据库: {tech_stack.get('database')} Client

## 3. 部署流程

### 3.1 基础设施搭建
1. 准备服务器资源或云资源
2. 安装 {tech_stack.get('container')} 和 {tech_stack.get('deployment')} 环境
3. 配置网络和安全组

### 3.2 中间件部署
1. 部署 {tech_stack.get('database')} (建议使用高可用模式)
2. 部署 {tech_stack.get('message_queue')}
3. 部署 {tech_stack.get('cache')}

### 3.3 应用部署
1. 构建应用镜像
2. 推送至镜像仓库
3. 更新 {tech_stack.get('deployment')} 配置文件
4. 执行滚动更新

## 4. 监控与运维

### 监控策略
- 部署监控代理 (Agent)
- 配置关键指标告警 (CPU, Memory, Disk, Network)
- 配置应用健康检查

### 备份策略
- 数据库每日全量备份
- 关键配置定期备份

## 5. 部署建议与注意事项

{tips_content}

---

**创建日期**: {datetime.now().strftime('%Y-%m-%d')}
**版本**: v1.0
**作者**: AI架构设计助手
"""
        except Exception as e:
            logger.error(f"部署文档备用内容生成失败: {e}")
            return f"# 部署指南\\n\\n由于生成过程中出现错误，这里提供简化的部署指南。\\n\\n**错误信息**: {str(e)}\\n\\n**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def _format_architecture_document(self, content: str) -> str:
        """格式化架构设计文档"""
        try:
            # 首先确保content是字符串类型
            if not isinstance(content, str):
                content = str(content)
            
            # 基本的文档格式化
            if not content.strip():
                return "# 架构设计文档\\n\\n文档内容为空。"
            
            # 确保文档有基本的结构
            if not content.startswith("#"):
                content = f"# 系统架构设计说明书\n\n{content}"
            
            # 添加页脚信息
            if "**创建日期**" not in content:
                content += f"\n\n---\n\n**创建日期**: {datetime.now().strftime('%Y-%m-%d')}\n**版本**: v1.0"
            
            return content
            
        except Exception as e:
            logger.error(f"架构文档格式化失败: {e}")
            # 如果格式化失败，至少返回原始内容的字符串表示
            return str(content) if not isinstance(content, str) else content

    def _format_technology_selection(self, content: str) -> str:
        """格式化技术选型文档"""
        try:
            # 首先确保content是字符串类型
            if not isinstance(content, str):
                content = str(content)
            
            # 基本的文档格式化
            if not content.strip():
                return "# 技术选型说明书\\n\\n文档内容为空。"
            
            # 确保文档有基本的结构
            if not content.startswith("#"):
                content = f"# 技术选型说明书\n\n{content}"
            
            # 添加页脚信息
            if "**创建日期**" not in content:
                content += f"\n\n---\n\n**创建日期**: {datetime.now().strftime('%Y-%m-%d')}\n**版本**: v1.0"
            
            return content
            
        except Exception as e:
            logger.error(f"技术选型文档格式化失败: {e}")
            # 如果格式化失败，至少返回原始内容的字符串表示
            return str(content) if not isinstance(content, str) else content

    def _format_deployment_guide(self, content: str) -> str:
        """格式化部署指南"""
        try:
            # 首先确保content是字符串类型
            if not isinstance(content, str):
                content = str(content)
            
            # 基本的文档格式化
            if not content.strip():
                return "# 部署指南\\n\\n文档内容为空。"
            
            # 确保文档有基本的结构
            if not content.startswith("#"):
                content = f"# 系统部署指南\\n\\n{content}"
            
            # 添加页脚信息
            if "**创建日期**" not in content:
                content += f"\n\n---\n\n**创建日期**: {datetime.now().strftime('%Y-%m-%d')}\n**版本**: v1.0"
            
            return content
            
        except Exception as e:
            logger.error(f"部署指南格式化失败: {e}")
            return str(content) if not isinstance(content, str) else content

    async def _call_model_with_streaming(self, prompt: str) -> str:
        """调用模型，支持自动续写以解决截断问题"""
        full_content = ""
        # 初始消息列表
        messages = [{"role": "user", "content": prompt}]
        
        try:
            # 最多尝试3次续写 (1次初始 + 2次续写)
            for attempt in range(3):
                logger.debug(f"调用模型: {self.name} (尝试 {attempt + 1})")
                
                # 调用模型 (非流式调用，获取完整响应)
                response = await self.model(messages)
                
                # 提取本次生成的文本内容
                content = self._extract_content(response)
                
                # 累加内容
                full_content += content
                
                # 检查内容是否完整
                if self._is_complete(full_content):
                    break
                
                # 如果内容不完整，准备续写
                logger.info(f"检测到内容可能截断 (长度: {len(full_content)})，尝试续写...")
                
                # 将本次生成的内容加入历史
                messages.append({"role": "assistant", "content": content})
                # 添加续写指令
                messages.append({"role": "user", "content": "请继续完成上面的内容，直接接续，不要重复已生成的部分。"})
            
            # 最终检查
            if not self._is_complete(full_content):
                logger.warning(f"文档生成可能仍被截断，末尾字符: {full_content[-20:]}")
                # 尝试简单的补全
                if full_content.strip().endswith("|"):
                    full_content += "\n\n---"
            
            return full_content
            
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            # 如果已有部分内容，返回部分内容而不是报错
            if full_content:
                return full_content
            raise

    def _extract_content(self, response: Any) -> str:
        """从响应中提取文本内容"""
        if isinstance(response, str):
            return response
        
        # 处理 AgentScope ModelResponse 对象
        if hasattr(response, 'text') and response.text:
             return str(response.text)
             
        if hasattr(response, 'content'):
            if isinstance(response.content, str):
                return response.content
            elif isinstance(response.content, list):
                # 处理 [{"type": "text", "text": "..."}] 格式
                text = ""
                for item in response.content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text += item.get('text', '')
                return text
                
        # 尝试其他属性
        for attr in ['message', 'data', 'result']:
            if hasattr(response, attr):
                val = getattr(response, attr)
                if isinstance(val, str):
                    return val
                if hasattr(val, 'content'):
                    return str(val.content)
                    
        return str(response)

    def _is_complete(self, content: str) -> bool:
        """检查内容是否完整"""
        if not content:
            return False
        # 检查是否以常见的结束符结尾
        return content.strip().endswith(("。", ".", "!", "}", "]", ">", "```", "---", "**版本**: v1.0", "文档结束"))
