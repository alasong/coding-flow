# 智能软件开发工作流系统 🤖

基于AgentScope框架的多智能体协作系统，集成需求分析、架构设计与项目分解的完整端到端工作流，并生成技术文档套件。

## 🌟 核心功能

### 智能需求分析
- **多智能体协作**: 需求收集 → 分析 → 验证 → 文档生成
- **结构化输出**: 自动生成JSON和Markdown格式的需求规格说明书
- **需求条目化**: 将用户需求分解为可追踪的功能需求(FR)和非功能需求(NFR)

### 架构设计自动化
- **智能架构生成**: 基于需求分析结果自动生成系统架构
- **组件映射**: 智能匹配需求与架构组件，支持100%需求覆盖
- **架构验证**: 多维度评估架构设计的合理性和可行性

### 项目分解与并发
- **软件单元抽取**: 统一抽取系统组件、数据库对象、API端点为 `Software Unit`
- **工作包分解**: 按域/类型分桶，限制每包≤3单元，LLM友好粒度
- **覆盖度门禁**: 统计并保证 `Software Unit` 100%覆盖，自动补救未覆盖项
- **并发编排**: 基于上下文与资源冲突生成并发批次，输出冲突集

## ⭐ 核心功能
- 端到端工作流：需求→架构→项目分解→项目开发→项目部署，统一输入输出与追踪矩阵
- 多任务并行：支持同时运行多个需求任务，摘要与详情持久化，刷新/重启后可恢复
- 队列执行器：后台并发处理任务，避免阻塞；支持扩展到外部消息队列
- 智能分解与门禁：软件单元抽取、工作包规划、100%覆盖度校验与补救包自动生成
- 并发编排与资源锁：按上下文与资源冲突分批，数据库同表迁移互斥，共享资源锁定
- 开发脚手架生成：Web/CLI 模式自动决策，生成代码、测试、OpenAPI、迁移、CI、环境示例与验证报告
- 部署工件与预检：Dockerfile/Compose/Helm、多环境 `.env`、健康探针、预检脚本与报告；支持一键启动/停止环境
- 仪表盘与实时推送：WebSocket 实时任务列表与进展，指标与环境入口、工件目录直达
- CI 预检工作流：自动生成工件并运行构建/健康检查，上传报告作为构件
- 安全与配置治理：不提交真实密钥，示例 `.env.example` 与 `secrets.example`；换行符与忽略规则统一
- 可扩展性：Agent 插件化与配置开关，技术栈策略可替换（Python/FastAPI 等），易于接入更多服务与仓库

## 🔗 端到端工作流总览
- 步骤链路：
  1. 需求分解（RequirementAnalysisWorkflow）
  2. 架构设计分解（ArchitectureDesignWorkflow）
  3. 项目分解（ProjectDevelopmentWorkflow）
  4. 项目开发（DevelopmentExecutionWorkflow）
  5. 项目部署（DeploymentWorkflow）
- 输入/输出：
  - 需求输入：自由文本或文件（`-f requirements.txt`）
  - 架构输出：`output/<项目目录>/architecture_workflow_result_*.json`、设计与指南 Markdown
  - 分解输出：`output/<项目目录>/decomposition/*`（软件单元、工作包、覆盖度与并发报告）
  - 开发输出：`output/<项目目录>/development_execution/project_code/*`（代码、测试、OpenAPI、迁移、CI、环境示例、验证报告）
  - 部署输出：`output/<项目目录>/deployment/*`（Dockerfile/Compose/Helm、env、脚本、观测、预检与安全报告）
- 关键指标与环境：
  - 覆盖度（%）、工作包数量、并发批次数
  - 环境入口：`/ui`（前端）与 `/health`（健康检查）

### 运行方式（端到端）
```bash
python main.py -f requirements.txt -m sequential --show-mapping
```
或启动仪表盘：
```bash
python -m uvicorn server:app --reload --port 9000
```
访问 `http://localhost:9000/ui/` 提交需求并查看端到端进展、指标与环境入口。

### 界面与服务接口
- 仪表盘：`/ui`（任务列表、进展、指标、环境入口、工件链接）
- REST：
  - `POST /run` 创建任务 → `{ task_id }`
  - `GET /status` 任务摘要（支持持久化恢复）
  - `GET /status/{task_id}` 单任务详情（合并持久化信息）
  - `GET /metrics/{task_id}` 单任务指标（覆盖度/工作包/并发批次/环境）
  - `GET /details/{task_id}` 单任务工件入口（代码/部署/报告目录）
  - `POST /deploy/start/{task_id}`、`POST /deploy/stop/{task_id}` 启停Compose环境
- 文件直达：`/files/<相对output路径>`（代码、部署与报告目录）

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
| `decomposition` | 仅执行项目分解 | 通过主工作流步骤调用 |
| `development_execution` | 执行项目开发 | 通过主工作流步骤调用 |

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

系统将在 `output/<项目目录>/` 生成分项目的文档套件（不混放）：

### 需求分析结果
- `requirement_analysis_YYYYMMDD_HHMMSS.json` - 结构化需求数据
- `requirement_document_YYYYMMDD_HHMMSS.md` - 需求规格说明书

### 架构设计结果  
- `architecture_workflow_result_YYYYMMDD_HHMMSS.json` - 架构设计数据
- `architecture_design_document_YYYYMMDD_HHMMSS.md` - 架构设计文档

### 技术文档
- `technology_selection_document_YYYYMMDD_HHMMSS.md` - 技术选型说明
- `deployment_guide_YYYYMMDD_HHMMSS.md` - 部署指南

### 项目分解结果（位于 `output/<项目目录>/decomposition/`）
- `development_workflow_result_YYYYMMDD_HHMMSS.json` - 软件单元、工作包、覆盖度与并发批次
- `development_overview_YYYYMMDD_HHMMSS.md` - 项目分解总览（覆盖度、并发批次、工作包列表）

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
│ 需求分析工作流 │  │ 架构设计工作流 │  │ 项目分解工作流 │
│ Requirement   │  │ Architecture │  │ Decomposition │
│ Workflow      │  │ Workflow     │  │ Workflow      │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 多智能体协作
```
需求收集Agent ──→ 需求分析Agent ──→ 需求验证Agent ──→ 文档生成Agent
     │                │                │              │
     └────────────────┴────────────────┴────→ 协调器
```

## 🎯 端到端验证要点
 - 需求→架构：需求条目追踪矩阵，覆盖率统计与评分（100%）
 - 架构→分解：Software Unit 抽取与 Work Package 绑定（100%覆盖）
 - 并行能力：并发批次生成，冲突集识别（DB同表迁移互斥、共享资源锁）
 - 文档套件：架构设计/技术选型/部署指南 + 项目分解总览

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
│   ├── technical_document_generator.py # 技术文档生成智能体
│   ├── software_unit_extractor.py  # 软件单元抽取智能体
│   ├── work_package_planner.py     # 工作包规划智能体
│   ├── unit_workpackage_matcher.py # 单元-工作包匹配智能体
│   ├── coverage_auditor.py         # 覆盖度审计智能体
│   ├── concurrency_orchestrator.py # 并发编排智能体
│   └── dev_plan_generator.py       # 开发计划生成智能体
├── workflow/                        # 工作流定义
│   ├── master_workflow.py         # 主工作流协调器
│   ├── requirement_workflow.py    # 需求分析工作流
│   ├── architecture_workflow.py   # 架构设计工作流
│   └── development_workflow.py    # 项目分解工作流
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
    "enable_development_workflow": True,
    "save_intermediate_results": True
}

DEVELOPMENT_WORKFLOW_CONFIG = {
    "max_units_per_package": 3,
    "require_full_coverage": True
}
```

## 🐛 故障排除

### 常见问题

**Q: API调用失败怎么办？**
A: 检查API密钥配置，确保网络连接正常，查看日志文件获取详细信息。

**Q: 覆盖度未达100%怎么办？**  
A: 系统会自动生成补救包补齐未覆盖单元；也可调小 `max_units_per_package` 控制粒度后重跑。

**Q: 输出文档为空怎么办？**
A: 检查模型响应是否正常，使用 `--log-level DEBUG` 查看详细日志。

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进系统功能。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**
## 🧭 项目开发工作流（DevelopmentExecutionWorkflow）

- 输入：项目分解输出的 `software_units` 与 `work_packages`
- 输出：代码脚手架、API骨架、数据库迁移、测试套件、CI配置、运行验证报告
- 配置：`DEVELOPMENT_EXECUTION_CONFIG`（语言、覆盖率阈值、CI模板）

### 使用示例
执行完整顺序模式生成分解后，主工作流会串行触发项目开发工作流：
```bash
python main.py -f requirements.txt -m sequential
```
输出位于：`output/<项目目录>/development_execution/`

### 界面模式自动决策
- 规则：
  - 需求中出现“用户/界面/前端/页面/管理后台/web/ui/docs”等词 → 选择 Web 前端
  - 需求中出现“命令行/CLI/脚本/批处理/终端/shell”等词 → 选择 CLI
  - 若未明确，结合 `technology_stack.frontend` 判断；仍无法判断则默认 Web
- 生成结果：
  - Web 前端：`frontend/index.html`，后端挂载 `/ui`，访问 `http://localhost:8000/ui/`
  - CLI：`cli.py`（Typer），示例命令 `python cli.py health`

### 交付物清单（按项目目录）
- `project_code/app/main.py`：服务入口（含 `/health`）
- `project_code/openapi.json`：API 规范
- `project_code/migrations/0001_init.sql`：数据库迁移示例
- `project_code/tests/test_basic.py`、`project_code/test_report.md`：测试与报告
- `project_code/.github/workflows/ci.yml`：CI 配置（安装依赖 + 运行 pytest）
- `project_code/.env.example`：环境变量示例（不包含真实密钥）
- `project_code/README.md`：项目执行与说明（根据 Web/CLI 模式动态生成）

### 启动与验证
- 后端启动：
  ```bash
  uvicorn app.main:app --reload --port 8000
  # 健康检查
  curl http://localhost:8000/health
  ```
- Web 前端：访问 `http://localhost:8000/ui/`
- CLI：
  ```bash
  python cli.py health
  ```
- 测试：
  ```bash
  pytest -q
  ```

### 后续增强（可选）
- 前端工程化：升级为 React/Vite 或 Vue 标准项目结构、路由与页面骨架
- 测试与覆盖率：生成 JUnit/XML 与 HTML 覆盖率报告，在 CI 中归档
- 运行验证：容器化健康检查与端点自动化验证，生成详细运行报告

## 🚀 部署工作流（DeploymentWorkflow）
在项目开发完成后自动将 `project_code` 生成可部署制品与脚手架，并选择合适的部署模式。

### 部署模式
- Compose：适合单服务或低复杂度场景
- Kubernetes（Helm）：适合多服务、可扩展与滚动升级场景
- Bare-metal：未安装容器环境的回退方案（仍生成 Dockerfile）

### 输出目录
- `output/<项目目录>/deployment/`
  - `docker/Dockerfile`、`docker/docker-compose.yml`
  - `k8s/charts/...` 或 `k8s/manifests/*.yaml`
  - `env/{dev,staging,prod}.env`、`env/secrets.example`
  - `scripts/{deploy,rollback,migrate}.(sh|ps1)`
  - `observability/{prometheus.yml,grafana_dashboards/}`
  - `reports/{preflight.md,deployment_result.json}`

### 使用示例
```bash
python main.py -f requirements.txt -m sequential
```
执行完成后在对应项目目录的 `deployment/` 下查看部署工件。

### CI/CD 与门禁
- 生成 `cd/deploy.yml`（GitHub Actions），包含构建与发布占位
- 门禁：镜像构建、探针通过、迁移安全、密钥检查、基础安全扫描

### 集成验证（预检）
- 预检脚本：`deployment/scripts/preflight.(sh|ps1)`，本地构建镜像并运行健康检查
- 预检报告：`deployment/reports/preflight.md`，包含验证步骤与结果摘要

### CI 集成（预检）
- 工作流：`.github/workflows/deployment-preflight.yml`
- 行为：自动执行顺序工作流生成项目工件 → 运行预检脚本 → 上传 `preflight.md` 报告为构件
## 🖥️ Web 界面与端到端测试

- 启动界面服务：
  ```bash
  python -m uvicorn server:app --reload --port 9000
  ```
- 访问仪表盘：`http://localhost:9000/ui/`，可输入需求并运行端到端流程，查看各步骤进展与项目输出目录
- 多任务并行：支持同时运行多个需求任务；刷新后任务摘要可恢复（output/tasks_index.json），选中任务ID持久化到浏览器（localStorage）
- 实时更新：通过 WebSocket `/ws` 推送任务列表变更，界面自动刷新任务列表
- 端到端测试：
  ```bash
  python -m pytest -q tests/test_web_progress.py
  ```
### 持久化与队列执行
- 任务摘要持久化：`output/tasks_index.json`，服务器重启后可恢复
- 任务详情持久化：每个项目目录 `status.json`
- 队列执行器：`infra/queue.py`，并发工作协程；避免阻塞主线程
## 📦 快速开始
- 安装依赖：
  ```bash
  pip install -r requirements.txt
  ```
- 端到端运行（顺序模式）：
  ```bash
  python main.py -f requirements.txt -m sequential --show-mapping
  ```
- 启动仪表盘（多任务并行 + 实时推送）：
  ```bash
  python -m uvicorn server:app --reload --port 9000
  ```
  访问 `http://localhost:9000/ui/`，提交需求，查看各步骤进展、指标与环境入口，支持“启动/停止环境”。

## 🧩 核心能力总览
- 需求分解 → 架构设计分解 → 项目分解 → 项目开发 → 项目部署（端到端闭环）
- 多任务并行与持久化：`output/tasks_index.json`（摘要）、每项目 `status.json`（详情）
- 开发工件：项目代码（app/tests/openapi/migrations/CI/env），测试与报告
- 部署工件：Dockerfile/Compose/Helm、多环境 `.env`、预检脚本与报告、CD占位
- 界面：实时任务列表（WebSocket）、任务指标（覆盖度/工作包/并发批次）、环境入口（UI/Health）、工件目录直达

## 🔧 提交前检查
- 清理生成物：确保 `output/` 已清空（已在 `.gitignore` 排除）
- 换行符规范：`.gitattributes` 已配置（代码LF，Windows脚本CRLF）
- 密钥安全：不提交任何真实密钥；仅 `.env.example` 与 `secrets.example`
- 已暂存状态：
  ```bash
  git add -A
  git status -s
  ```
- 提交与推送：
  ```bash
  git commit -m "feat: workflows, deployment, UI, persistence, cleanup"
  git remote add origin <your_repo_url>
  git push -u origin main
  ```

## 🚀 CI 预检与验证
- 工作流：`.github/workflows/deployment-preflight.yml`
- 动作：顺序生成工件 → 运行预检脚本（构建镜像、容器健康检查）→ 上传 `preflight.md` 报告
- 触发：推送到 `main` 或手动 `workflow_dispatch`

## 📁 重要目录
- `workflow/`：各工作流（需求/架构/分解/开发/部署）
- `agents/`：Agent 实现（抽取/规划/匹配/覆盖/并发/脚手架/迁移/CI/安全/预检）
- `server.py` + `dashboard/`：多任务仪表盘与实时推送/环境控制
- `infra/`：持久化与简易队列执行器
- `output/`：分项目输出目录（不提交）
