# coding-flow 架构审查报告

本报告基于对 `coding-flow` 项目代码的深度审查，旨在识别架构不足并提出改进建议。该项目基于 AgentScope 框架，旨在实现从需求分析到部署的端到端自动化。

## 1. 核心架构问题

### 🚨 抽象层断裂 (Orphaned Abstractions)
项目定义了基类但未被核心逻辑使用，导致接口不统一。
- **现象**: 存在 `BaseWorkflow` 和 `BaseAgent`，但核心业务类如 `RequirementAnalysisWorkflow` 和 `RequirementAnalyzerAgent` **并未继承**这些基类。
- **后果**:
  - 代码存在两套平行的类层级，增加了维护认知负荷。
  - `MasterWorkflow` 中不得不针对每个子工作流写死调用逻辑，无法利用多态性。

### 🔗 高耦合的编排逻辑 (Tight Coupling)
主工作流 (`MasterWorkflow`) 与子工作流的实现细节过度耦合。
- **现象**: `MasterWorkflow.run` 方法中充斥着对特定子工作流的硬编码调用和数据提取逻辑。
- **后果**: 新增或修改一个工作流步骤需要修改 `MasterWorkflow` 的核心代码，违反了**开闭原则 (Open-Closed Principle)**。

### 🧩 脆弱的数据流转 (Fragile Data Flow)
步骤间的数据传递依赖隐式的字典键值约定。
- **现象**: 大量使用 `dict.get("key", {})` 进行防御性编程，且数据结构在不同步骤间没有明确的契约（Schema）。
- **后果**: 难以追踪数据流向，重构风险高，缺乏类型安全。

## 2. 代码质量与实现细节

### 🛠️ 硬编码配置 (Hardcoded Configuration)
- **现象**: Agent 的模型配置直接写在 `__init__` 方法中。
- **后果**: 难以在测试环境切换 Mock 模型，也难以灵活调整参数。

### 🔍 启发式逻辑的局限性 (Heuristic Logic)
- **现象**: 需求与架构的映射依赖硬编码的关键词列表。
- **后果**: 这种基于规则的匹配非常脆弱，无法理解语义。

### ⚠️ 错误处理不足
- **现象**: 大部分错误处理仅是打印日志，缺乏恢复机制。

## 3. 改进计划 (Refactoring Roadmap)

### ✅ 第一阶段：统一抽象与接口 (已开始)
1.  **激活基类**: 让所有子工作流继承 `BaseWorkflow`，所有 Agent 继承统一的 `BaseAgent`。
2.  **标准化接口**: 定义统一的 `execute(context: Context) -> Result` 接口（支持异步）。
3.  **人机交互**: 在需求分析阶段增加 Review Points 生成与人工确认环节。

### ✅ 第二阶段：解耦主工作流
1.  **管道模式**: 将 `MasterWorkflow` 重构为管道模式，动态注册步骤。
2.  **数据类封装**: 使用 Pydantic 定义上下文数据结构。

### ✅ 第三阶段：增强核心逻辑
1.  **语义搜索**: 使用 Embedding 替代关键词匹配。
2.  **配置外置**: 提取模型配置到配置文件。

## 4. 实施状态
- [x] 重构 `BaseWorkflow` 为异步接口。
- [x] 在 `RequirementAnalysisWorkflow` 中实现 `BaseWorkflow` 接口。
- [x] 在 `ArchitectureDesignWorkflow` 中实现 `BaseWorkflow` 接口。
- [x] 增加需求分析阶段的人机交互 Review Points。
- [ ] 统一 Agent 抽象层。
- [ ] 实现项目规则 Hook (清理与文档刷新)。
