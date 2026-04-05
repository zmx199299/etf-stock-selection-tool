# AGENTS.md - ETF 场内基金智能分析系统 项目规则

## 语言

所有回答和代码注释必须使用**中文**。

## 项目架构

前端 Vue 3 (Tauri 2) <---> Rust 中间层 (进程管理 & IPC) <---> Python 引擎 (JSON-RPC over stdin/stdout)

## 核心开发纪律

### 1. 测试驱动开发 (TDD)

**重要：所有代码的 TDD 规则必须与 Superpowers 的 TDD 技能要求一致。**

对任何代码的修改，必须严格遵循 TDD 流程：
1. **RED**：先写（或修改）测试，运行并观察失败。
2. **GREEN**：编写/修改最少量代码使测试通过。
3. **REFACTOR**：在测试全绿的前提下重构代码。

每次提交代码前，必须运行相应的测试命令确认全量测试通过：
- Python 后端：`pytest src-python/tests/`
- Rust 中间层：`cargo test` 或 `cargo check`（视环境而定）
- 前端构建验证：`npm run build`

### 2. 跨栈修改与冷备份协议

当修改涉及"前后端数据结构联动"、"重构"或"高风险变更"时：
1. **修改前**：使用 `tar -czf backups/<描述>_$(date +%Y%m%d%H%M%S).tar.gz <目标目录>` 进行冷备份。
2. **修改中**：严格遵循 TDD 流程修改后端，再同步前端。
3. **修改失败时**：直接从 `backups/` 解压回滚，保证 Git 工作区干净。

> `backups/` 已加入 `.gitignore`，不参与版本管理。

详见 `docs/development/protocols/cross_stack_modification.md`。

### 3. 前端 UI 确认约束

- **先原型后实现**：前端页面永远先用 Mock 数据展示骨架给用户确认，获得明确认可后再对接真实后端或实现复杂可视化（如 ECharts）。
- **不得擅自推进**：在用户未确认页面的表格样式、布局细节、按钮去留之前，禁止自行推进与该页面深度绑定的后续开发。

### 4. 色彩方案

盈亏显示的色彩方案（红涨绿跌 / 绿涨红跌）必须是**用户可配置**的，不得硬编码为任何一种。实现为全局设置，所有页面统一响应。

## 文档维护

项目文档分为两套，完成每个阶段或有重大结构更改时必须同步更新：
- **人类阅读版**：`docs/development/human/` — 面向开发者和用户的开发日志与计划。
- **AI 上下文版**：`docs/development/ai/` — 面向 AI 助手的项目状态摘要与指令。

## 持续日志机制

### 功能级更新
每完成一个具体功能点或模块，主动在 `docs/development/human/` 的当日日志中追加记录，同时同步更新 `docs/development/ai/` 对应的上下文摘要，即便用户没有提醒。

### 每日收尾提醒 (22:00+ Rule)
当对话发生在**北京时间 22:00 之后**时，必须主动提示用户：

> "当前时间已较晚，是否需要我为您生成【今日开发代办清单】与【明日开发计划】，并记录到开发日志中？"

用户同意后执行收尾日志写入。

## 环境约束

不同开发者的本地环境可能存在差异，以下为通用约束：
- **Python 端验证**：统一使用 `pytest src-python/tests/` 运行测试。
- **Rust 端验证**：若本地缺少 GTK/GDK 等 GUI 依赖导致 `cargo test` 或 Tauri 编译失败，可退而使用 `cargo check` 进行类型检查验证。能完整编译的环境应优先使用 `cargo build` / `cargo test`。
- **前端验证**：统一使用 `npm run build`（`vue-tsc --noEmit && vite build`）检查 TypeScript 类型和构建产物。

## 关键目录

| 路径 | 用途 |
|---|---|
| `src-python/` | Python 引擎（JSON-RPC 服务端、数据源、技术分析、评分） |
| `src-python/tests/` | Python 单元测试 |
| `src-tauri/src/` | Rust 中间层（进程管理、Tauri Commands） |
| `src/views/` | Vue 3 前端页面 |
| `docs/development/` | 开发文档（human/ 和 ai/ 两套） |
| `docs/development/protocols/` | 开发协议与规范 |
| `backups/` | 冷备份目录（不入 Git） |