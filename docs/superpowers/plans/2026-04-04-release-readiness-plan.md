# FUNDFLOW 可交付收尾计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 P1 Analysis 真实接口完成的基础上，补齐业务能力、桌面端真实链路与交付收尾工作，使 FUNDFLOW 从“可演示/可内测”推进到“可稳定交付”。

**Architecture:** 以现有 Vue 3 + Tauri + Python JSON-RPC 架构为基础，不再重做页面骨架，优先补业务逻辑与真实运行链路。先补 P2 业务核心，再做 Tauri/Rust 端到端收口，最后处理发布打包与交付文档。

**Tech Stack:** Vue 3、TypeScript、Vitest、Tauri 2、Rust、Python、pytest、SQLite、AKShare

---

## 剩余工作分层

### A. 高优先级：决定软件是否“真的可用”

- [ ] 细化 `Scorer`，让评分不再是当前过于简化的占位实现
- [ ] 细化 `AnalysisService` 的 `strategy` 与 `risk_level`，从稳定占位文案升级为真实业务输出
- [ ] 验证并收口 Tauri/Rust -> Python 引擎真实运行链路，包括首启、空库预热、异常提示

### B. 中优先级：决定软件是否“完整”

- [ ] 继续真实化剩余接口：`get_screening_results`、`get_scoring_data`、`get_scheduler_data`
- [ ] 补全桌面端异常处理、同步进度、用户提示和失败恢复策略

### C. 交付优先级：决定软件是否“能发布”

- [ ] 整理版本信息、发布说明、安装包打包流程
- [ ] 做一轮发布前全链路验证与文档收口

---

## 推荐执行顺序

### Task 1: 评分与策略业务真实化

**目标:** 去掉当前最明显的“占位业务”部分，让 Analysis 与评分结果具备实际参考意义。

**涉及文件：**
- `src-python/engine/scoring/scorer.py`
- `src-python/engine/services/analysis_service.py`
- `src-python/engine/services/fund_service.py`
- `src-python/tests/test_scorer.py`
- `src-python/tests/test_analysis_service.py`
- `src-python/tests/test_fund_service.py`

**完成标准：**
- `score` 不再是简单固定/粗略返回，而是基于已有技术指标与规则输出可解释分数
- `risk_level` 有明确规则，不再只是稳定占位文案
- `strategy` 的七个字段有真实推导逻辑，而不是静态模板
- 对应测试补齐并通过

### Task 2: Tauri / Rust 真实链路收口

**目标:** 确认桌面端不是“前后端各自通过”，而是真的能从 UI 打到 Rust，再打到 Python。

**涉及文件：**
- `src-tauri/src/engine.rs`
- `src-tauri/src/lib.rs` 或相关 command 注册文件
- `src-python/main.py`
- 相关 Rust 测试或检查文件

**完成标准：**
- `invoke_engine` 能稳定调用 `get_fund_list`、`get_dashboard_signals`、`search_funds`、`get_fund_analysis`
- 空数据库首启时的预热行为可验证
- Python 引擎启动失败、同步失败、返回异常时有可接受的前端/桌面端表现
- 至少运行一次 `cargo check`，环境允许时运行 `cargo test` 或实际启动 Tauri

### Task 3: 剩余接口真实化

**目标:** 把还停留在硬编码/Mock 的核心业务接口逐步拉到真实服务层。

**涉及文件：**
- `src-python/engine/server.py`
- 新增或扩展对应 service 文件
- `src-python/tests/test_server*.py`
- 对应前端页/工具层（如果已有消费方）

**完成标准：**
- 至少明确每个剩余接口是“本阶段实现”还是“明确延期”
- 若实现，则必须有真实 service 路径与测试
- 若延期，则文档中明确说明原因和优先级

### Task 4: 真实环境异常体验补齐

**目标:** 把“能跑”提升到“用户知道发生了什么”。

**涉及文件：**
- `src/views/*.vue` 中与真实接口相关的页面
- 对应 `src/utils/*.ts`
- 对应前端测试文件

**完成标准：**
- 首次同步/等待中有清晰状态提示
- 接口失败时不出现误导性“假成功”体验
- 无数据、加载中、错误态三者可区分

### Task 5: 发布收尾与验收

**目标:** 让软件具备交付条件，而不只是代码完成。

**涉及文件：**
- `docs/development/ai/current_state.md`
- `docs/development/human/` 下当日日志与验收记录
- 打包相关配置文件

**完成标准：**
- 运行并记录：
  - `pytest src-python/tests/`
  - `npm test -- --run`
  - `npm run build`
  - `cargo check` / `cargo test`（按环境）
- 形成版本说明、已知限制与下一步路线
- 如需要发布，补齐打包与安装说明

---

## 当前判断

- [ ] **内测可用标准**
  - 还缺：评分/策略真实化 + Tauri 真实链路验收

- [ ] **正式交付标准**
  - 还缺：上述内容 + 剩余接口真实化 + 异常体验补齐 + 发布收尾

---

## 建议结论

- [ ] 先把 Task 1 和 Task 2 做完，再重新评估是否进入“可内测”状态
- [ ] 若目标是尽快给少量用户试用，优先做：评分/策略真实化、Tauri 链路验证、错误态补齐
- [ ] 若目标是完整版本交付，则继续完成 Task 3 到 Task 5
