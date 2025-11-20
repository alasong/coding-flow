# 智能软件开发工作流系统 🤖

基于AgentScope框架的多智能体协作系统，集成需求分析、架构设计和技术文档生成的完整开发生命周期管理。

## 🌟 核心功能

### 智能需求分析
- **多智能体协作**: 需求收集 → 分析 → 验证 → 文档生成
- **结构化输出**: 自动生成JSON和Markdown格式的需求规格说明书
- **需求条目化**: 将用户需求分解为可追踪的功能需求(FR)和非功能需求(NFR)

### 架构设计自动化
- **智能架构生成**: 基于需求分析结果自动生成系统架构
- **组件映射**: 智能匹配需求与架构组件，支持100%需求覆盖
- **架构验证**: 多维度评估架构设计的合理性和可行性

### 技术文档生成
- **完整文档套件**: 架构设计文档、技术选型说明、部署指南
- **智能内容生成**: 基于架构设计自动生成技术文档
- **多格式支持**: 支持Markdown、JSON等多种输出格式

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API密钥
```bash
# 创建配置文件
cp .env.example .env

# 编辑 .env 文件，配置API密钥
# 支持DashScope和OpenAI
DASHSCOPE_API_KEY=your_api_key_here
# 或
OPENAI_API_KEY=your_openai_key_here
```

### 交互式使用
```bash
# 启动交互式模式
python main.py
```

### 批量处理
```bash
# 使用需求文件批量处理
python main.py -f requirements.txt -m sequential

# 带调试信息的完整模式
python main.py -f requirements.txt -m sequential --debug-requirements --debug-architecture --show-mapping --validate-coverage
```

## 📋 工作流模式

| 模式 | 描述 | 命令 |
|------|------|------|
| `sequential` | 顺序执行：需求分析 → 架构设计 | `-m sequential` |
| `parallel` | 并行执行需求和架构分析 | `-m parallel` |
| `requirement_only` | 仅执行需求分析 | `-m requirement_only` |
| `architecture_only` | 仅执行架构设计 | `-m architecture_only` |

## 🛠️ 高级功能

### 调试和验证
```bash
# 显示详细需求信息
--debug-requirements

# 显示架构组件匹配详情  
--debug-architecture

# 显示需求-架构映射关系
--show-mapping

# 验证需求覆盖率
--validate-coverage

# 设置日志级别
--log-level DEBUG
```

### 系统信息
```bash
# 查看工作流系统信息
python main.py --info
```

## 📊 输出结果

系统将在 `output/` 目录生成完整的文档套件：

### 需求分析结果
- `requirement_analysis_YYYYMMDD_HHMMSS.json` - 结构化需求数据
- `requirement_document_YYYYMMDD_HHMMSS.md` - 需求规格说明书

### 架构设计结果  
- `architecture_workflow_result_YYYYMMDD_HHMMSS.json` - 架构设计数据
- `architecture_design_document_YYYYMMDD_HHMMSS.md` - 架构设计文档

### 技术文档
- `technology_selection_document_YYYYMMDD_HHMMSS.md` - 技术选型说明
- `deployment_guide_YYYYMMDD_HHMMSS.md` - 部署指南

### 综合报告
- `master_workflow_result_YYYYMMDD_HHMMSS.json` - 完整工作流结果
- `master_workflow_summary_YYYYMMDD_HHMMSS.md` - 执行摘要

## 🏗️ 系统架构

### 智能体(Agent)架构
```
┌─────────────────────────────────────────────────────────┐
│                   主工作流协调器                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │              MasterWorkflow                       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
│ 需求分析工作流 │  │ 架构设计工作流 │  │ 技术文档生成  │
│ Requirement   │  │ Architecture │  │ Technical    │
│ Workflow      │  │ Workflow     │  │ Documents    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 多智能体协作
```
需求收集Agent ──→ 需求分析Agent ──→ 需求验证Agent ──→ 文档生成Agent
     │                │                │              │
     └────────────────┴────────────────┴────→ 协调器
```

## 🎯 核心优势

- ✅ **100%需求覆盖率**: 智能算法确保每个需求都有对应的架构设计
- ✅ **真实API集成**: 支持DashScope和OpenAI等大模型API
- ✅ **异步处理**: 完全异步架构，支持高并发处理
- ✅ **错误恢复**: 完善的错误处理和重试机制
- ✅ **可扩展**: 模块化设计，易于添加新的智能体和工作流
- ✅ **多格式输出**: 支持JSON、Markdown等多种文档格式

## 📁 项目结构

```
├── main.py                          # 主程序入口
├── config.py                        # 系统配置
├── requirements.txt                 # 项目依赖
├── agents/                          # 智能体实现
│   ├── requirement_collector.py     # 需求收集智能体
│   ├── requirement_analyzer.py    # 需求分析智能体  
│   ├── requirement_validator.py   # 需求验证智能体
│   ├── architecture_analyzer.py   # 架构分析智能体
│   ├── architecture_validator.py  # 架构验证智能体
│   └── technical_document_generator.py # 技术文档生成智能体
├── workflow/                        # 工作流定义
│   ├── master_workflow.py         # 主工作流协调器
│   ├── requirement_workflow.py    # 需求分析工作流
│   └── architecture_workflow.py   # 架构设计工作流
├── utils/                           # 工具函数
└── output/                        # 输出目录
```

## 🔧 配置选项

### 模型配置
```python
# 支持的模型类型
MODEL_TYPES = ["dashscope", "openai", "mock"]

# 默认模型
DEFAULT_MODEL = "qwen-turbo"

# 模型参数
MODEL_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 30
}
```

### 工作流配置
```python
# 启用/禁用工作流
MASTER_WORKFLOW_CONFIG = {
    "enable_requirement_workflow": True,
    "enable_architecture_workflow": True,
    "save_intermediate_results": True
}
```

## 🐛 故障排除

### 常见问题

**Q: API调用失败怎么办？**
A: 检查API密钥配置，确保网络连接正常，查看日志文件获取详细信息。

**Q: 需求覆盖率低怎么办？**  
A: 使用 `--debug-requirements` 和 `--debug-architecture` 参数查看详细匹配过程，优化需求描述。

**Q: 输出文档为空怎么办？**
A: 检查模型响应是否正常，使用 `--log-level DEBUG` 查看详细日志。

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进系统功能。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**