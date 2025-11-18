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
    }
}