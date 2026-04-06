# Scoring 页面真实化设计方案 (2026-04-06)

## 1. 背景与目标
在 Phase 3 前端落地完成基础结构（Dashboard/FundList/Settings）后，目前 `Scoring (评分详情)` 页面完全采用前端的 `mockScoringData` 占位数据，未接入真实数据库。
本设计的目的是将前后端评分数据打通：后端组装真实的基础行情、技术评分和基于策略计算的动态交易建议，前端移除伪数据，完成渲染与真实后端 API 交互对接，实现高质量的 TDD 工程闭环。

## 2. 后端架构设计 (AnalysisService)
在 `src-python/engine/services/analysis_service.py` 中新增 `get_scoring_data(code: str)` 接口提供全量评分详情：

### 2.1 依赖与组装逻辑
- **基础信息**：通过传递 `code` 从 DB 表（如 `funds`, `daily_quotes`）查询最新的 `name`, `price`, `change`。
- **技术评分**：通过调用现有 `Scorer.score(df)` 获取 4 维度分数 (`trend_score`, `momentum_score`, `volatility_score`, `volume_score`) 及看多看空信号。
- **动态交易建议（策略计算）**：
  - `advice_amount`（建议买入量）：基于固定基准（例如预设投资本金 10000 元），计算方式：`10000 / (当前价格 * 100)` 取整 * 100 份。
  - `estimate_fee`（预估费用）：简单估算，例如：`买入量 * 价格 * (万1佣金 + 千1滑点)`，默认万 1 + 万 1。
  - `stop_loss`（止损价）：设定在当前价格下方 5% (`price * 0.95`)。
  - `take_profit`（止盈价）：设定在当前价格上方 10% (`price * 1.10`)。

### 2.2 RPC 层开放
在 `src-python/engine/server.py` 内：
- 清理掉外层文件顶部的废弃 mock `get_scoring_data`。
- 在 `create_real_server()` 内部注入 `analysis_service` 后，将 `"get_scoring_data"` 注册到 `analysis_service.get_scoring_data`。

## 3. 前端交互对接 (Scoring.vue)
- **数据流更新**：
  - 彻底删除 `import.meta.env.DEV` 阻断逻辑和 `mockScoringData` 常量。
  - 使用 `@tauri-apps/api/core` 的 `invoke('invoke_engine')` 发起调用。
- **字段适配器**：
  在获取到后端的 `snake_case` 返回值后，由于 Vue 响应式数据绑定了 `camelCase` 属性（如 `trendScore`、`adviceAmount`），在 `try-catch` 块中进行简单的映射适配。
- **UI 完善**：
  引入 `isLoading` 与 `errorMsg` 的状态控制，防止空内容渲染崩溃，确保加载态反馈友好。

## 4. TDD 测试规划
- **后端 TDD (pytest)**：
  - 新增 `test_analysis_service.py` 中 `test_get_scoring_data` 测试，断言返回字典必定包含所有的 12 个键（code, name, price, change, trend_score, etc...）。
  - 新增/更新 `test_server.py` 中 `test_create_real_server` 的注册校验。
- **前端 TDD (vitest)**：
  - 修改 `src/views/__tests__/Scoring.spec.ts` （如不存在则新增），测试 UI 组件渲染，验证 `invoke_engine` 是否被正确调用。
  - 测试断言加载状态的展示、成功数据的呈现（尤其是四个分数维度的对应），以及报错时的错误提示。
