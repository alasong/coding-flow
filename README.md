# 软件需求分析工作流系统

基于AgentScope框架的多智能体需求分析系统，支持真实大模型API集成。

## 功能特性

- ✅ 多智能体协作的需求分析流程
- ✅ 自动化需求收集、分析、验证和文档生成
- ✅ 支持DashScope和OpenAI真实大模型API
- ✅ 流式响应和非流式响应处理
- ✅ 结构化的需求文档输出（JSON和Markdown格式）
- ✅ 错误处理和日志记录

## 最新更新

### 2024-11-18
- **修复**：DashScopeChatModel协程调用问题，支持异步响应处理
- **优化**：工作流数据传输，避免请求体过大
- **增强**：所有Agent的响应处理能力，支持流式和非流式响应
- **验证**：真实API集成测试通过，可生成完整需求分析文档

## 安装

```bash
pip install -r requirements.txt
```

## 配置API密钥

在使用前，请配置您的API密钥：

```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，选择以下任一方式配置：
# 1. DashScope API (推荐)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# 2. OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

## 使用

### 基本使用
```bash
python main.py
```

### 自定义需求输入
编辑 `main.py` 文件，修改 `user_input` 变量：
```python
user_input = "您的具体需求描述"
```

## 输出结果

系统将在 `output/` 目录下生成：
- `requirement_analysis_YYYYMMDD_HHMMSS.json` - 完整的需求分析结果
- `requirement_document_YYYYMMDD_HHMMSS.md` - 格式化的需求规格说明书

## 项目结构

```
├── requirements.txt          # 项目依赖
├── main.py                   # 主程序入口
├── config.py                 # 配置文件
├── agents/                   # Agent定义
│   ├── __init__.py
│   ├── requirement_collector.py
│   ├── requirement_analyzer.py
│   ├── requirement_validator.py
│   └── document_generator.py
├── workflow/                 # 工作流定义
│   ├── __init__.py
│   └── requirement_workflow.py
└── utils/                    # 工具函数
    ├── __init__.py
    └── common.py
```

## Agent角色

1. **需求收集Agent** - 负责收集和整理用户需求
2. **需求分析Agent** - 分析需求的可行性和完整性
3. **需求验证Agent** - 验证需求的正确性和一致性
4. **文档生成Agent** - 生成结构化的需求文档

## 配置

在使用前，请配置您的API密钥：

```bash
# 创建 .env 文件
cp .env.example .env
# 编辑 .env 文件，添加您的API密钥
```