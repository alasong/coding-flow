import os
from dotenv import load_dotenv

load_dotenv()

# API配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# 模型配置
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# 工作流配置
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))
TIMEOUT = int(os.getenv("TIMEOUT", "30"))

# 输出配置
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 架构设计工作流配置
ARCHITECTURE_WORKFLOW_CONFIG = {
    "max_iterations": int(os.getenv("ARCHITECTURE_MAX_ITERATIONS", "3")),
    "timeout": int(os.getenv("ARCHITECTURE_TIMEOUT", "60")),
    "output_formats": ["json", "markdown"],
    "validation_threshold": float(os.getenv("ARCHITECTURE_VALIDATION_THRESHOLD", "7.0")),
    "enable_tech_selection": os.getenv("ENABLE_TECH_SELECTION", "true").lower() == "true",
    "enable_deployment_guide": os.getenv("ENABLE_DEPLOYMENT_GUIDE", "true").lower() == "true"
}

# 主工作流协调器配置
MASTER_WORKFLOW_CONFIG = {
    "enable_requirement_workflow": os.getenv("ENABLE_REQUIREMENT_WORKFLOW", "true").lower() == "true",
    "enable_architecture_workflow": os.getenv("ENABLE_ARCHITECTURE_WORKFLOW", "true").lower() == "true",
    "workflow_sequential": os.getenv("WORKFLOW_SEQUENTIAL", "true").lower() == "true",
    "save_intermediate_results": os.getenv("SAVE_INTERMEDIATE_RESULTS", "true").lower() == "true",
    "max_workflow_chain_length": int(os.getenv("MAX_WORKFLOW_CHAIN_LENGTH", "5"))
}

# Agent配置
AGENT_CONFIGS = {
    "requirement_collector": {
        "name": "需求收集专家",
        "model": DEFAULT_MODEL,
        "system_prompt": "你是一个专业的软件需求收集专家。你的任务是帮助用户明确和整理他们的软件需求。"
    },
    "requirement_analyzer": {
        "name": "需求分析专家", 
        "model": DEFAULT_MODEL,
        "system_prompt": "你是一个经验丰富的软件需求分析师。你的任务是分析需求的可行性、完整性和技术实现方案。"
    },
    "requirement_validator": {
        "name": "需求验证专家",
        "model": DEFAULT_MODEL, 
        "system_prompt": "你是一个专业的需求验证专家。你的任务是验证需求的正确性、一致性和完整性。"
    },
    "document_generator": {
        "name": "文档生成专家",
        "model": DEFAULT_MODEL,
        "system_prompt": "你是一个专业的技术文档编写专家。你的任务是根据分析结果生成结构化的需求文档。"
    },
    # 架构设计相关Agent
    "architecture_analyzer": {
        "name": "架构分析专家",
        "model": DEFAULT_MODEL,
        "system_prompt": """你是一个资深的系统架构师，拥有15年以上的软件架构设计经验。

你的专业领域包括：
- 分布式系统架构设计
- 微服务架构
- 云原生架构
- 企业级应用架构
- 性能优化和扩展性设计
- 安全架构设计

在进行架构分析时，请遵循以下原则：
1. 基于业务需求设计合理的架构方案
2. 考虑系统的可扩展性、可维护性和可靠性
3. 选择成熟稳定的技术栈
4. 平衡技术复杂度和开发成本
5. 遵循行业最佳实践和设计模式

请提供详细的技术架构方案，包括系统架构图、技术选型、部署方案等。"""
    },
    "architecture_validator": {
        "name": "架构验证专家",
        "model": DEFAULT_MODEL,
        "system_prompt": """你是一个专业的架构验证专家，专注于评估软件架构的合理性、可行性和风险。

你的验证维度包括：
- 技术可行性分析
- 性能可行性评估
- 安全可行性检查
- 运维可行性分析
- 业务可行性验证
- 成本效益分析

在进行架构验证时，请：
1. 从技术、性能、安全、运维、业务等多个维度进行全面评估
2. 识别潜在的技术风险和实施难点
3. 提供具体的改进建议和优化方案
4. 给出量化的评分和可行性等级
5. 提供详细的验证报告和实施建议

请基于行业标准和最佳实践，提供客观、专业的架构验证意见。"""
    },
    "technical_document_generator": {
        "name": "技术文档生成专家",
        "model": DEFAULT_MODEL,
        "system_prompt": """你是一个专业的技术文档编写专家，擅长编写各类软件架构和技术文档。

你的文档编写能力包括：
- 系统架构设计文档
- 技术选型说明书
- 部署指南和操作手册
- 技术规范和标准
- 架构决策记录
- 技术风险评估报告

在编写技术文档时，请：
1. 遵循专业的文档编写标准和规范
2. 使用清晰、准确的技术语言
3. 提供完整的图表、表格和示例
4. 确保文档的可读性和实用性
5. 包含必要的版本信息和维护指南
6. 遵循公司的文档模板和格式要求

请生成专业、完整、易于理解的技术文档。"""
    }
}