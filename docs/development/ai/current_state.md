# ETF 智能分析系统 - AI 当前状态指针

**最后更新**: 2026-04-04 22:20 (UTC+8)

## 1. 当前阶段

当前阶段为 **P2 真实链路收口已完成，处于提交 / 发布前最终验证完成状态**。

## 2. 当前已完成内容

### Page 1 — 今日行情 (Dashboard)
- `Dashboard.vue` 展示共享基金卡片信号总览，支持全部/T+0/T+1 筛选。
- 卡片区采用均布网格布局，已移除首页独有的止损点展示。
- 已接入全局 `红多 / 绿多` 配色，与 `useColorModeStore()` 联动。
- 已接入 `useDisplaySettingsStore().cardCount` 控制展示卡片数量（替代硬编码 10）。

### Page 2 — 全量基金 (FundList)
- `FundList.vue` 宽表格页面已完成，包含搜索、空状态与雪球详情入口。
- 顶部业务文案已改为"全量场内基金（不含货币/债券基金）/ 共监测X支"。
- 作为当前最稳定的视觉基线，后续页面参照其横栏与容器结构。

### Page 3 — 技术分析 (Analysis)
- `Analysis.vue` 研究报告主线型 Mock 页面，统一到 FundList 的页面壳层节奏。
- 双页态：无 `code` 时为卡片入口页，有 `code` 时为纯详情页。
- 顶部入口承接首页共享基金卡片数据，已接入 `displaySettings.cardCount` 控制入口卡片数量。
- 图表区支持九种周期切换（分时/日K/5分/60分/120分/周K/月K/季K/年K），含 hover 浮层。
- 与首页统一通过 `loadSharedFundCards()` 读取同源卡片数据。

### Page 4 — 系统设置 (Settings) ✅ 新完成
- `Settings.vue` 三卡片布局：显示偏好、关于、隐私与免责声明。
- **显示偏好卡片**：
  - 涨跌配色（红多/绿多）切换，复用 `useColorModeStore()`，与 Page 2/3 顶栏按钮全局同步。
  - 卡片数量下拉（6/8/10/12），使用新建的 `useDisplaySettingsStore()`，联动 Dashboard 和 Analysis。
- **关于卡片**：2x2 网格展示 FUNDFLOW、v0.0.1 预览版、GPLv3、联网行为。
- **隐私与免责声明卡片**：三段声明（蓝/黄/红圆点标识）。

### 基础设施
- `useColorModeStore()` — 全局红多/绿多配色管理，localStorage 持久化。
- `useDisplaySettingsStore()` — 全局卡片数量设置管理，localStorage 持久化。
- `dashboardSignals.ts` — 共享基金卡片数据源与加载器，`getAnalysisEntryCards()` 支持 `count` 参数。
- `DataSyncPipeline` — 后端数据同步管道，支持基金列表、日线行情、净值同步到 SQLite。
- `FundService` — 后端业务层，支持基金列表、指标计算、FundList 所需的技术指标文字化与评分映射。
- `create_real_server()` — 后端真实服务装配入口，已可返回真实 `get_fund_list`、`get_dashboard_signals`、`search_funds`、`get_fund_analysis`、`get_scoring_data`、`get_screening_results`、`get_scheduler_data` 数据。
- `AnalysisService` — 已支持 Analysis 页面九周期真实数据：`intraday`、`day`、`m5`、`m60`、`m120`、`week`、`month`、`quarter`、`year`。
- `Scorer` / `AnalysisService.strategy` / `risk_level` — 已从占位逻辑升级为真实计算与降级保护逻辑。
- Rust `EngineManager` — 已支持自动启动、断连恢复、错误透传，前端无需手动先调用 `start_engine`。
- Tauri 默认构建资源已收口：补齐 `src-tauri/icons/icon.png` 占位图标，默认 `cargo check` / `cargo test` 可运行。
- 测试基线：前端 11 个测试文件，112 个测试用例全部通过；Python 端 49 个测试通过，2 个外部依赖测试按环境跳过；Rust 端 `cargo check` 通过，`cargo test` 通过（当前 0 个单元测试）。
- TypeScript 类型检查 + Vite 构建通过。

## 3. 当前约束

- 继续遵循 Mock 优先，不在用户确认前擅自推进真实数据联动或深度交互扩展。
- 后续页面统一遵循三区结构：左侧导航栏固定不改；顶部横栏风格与宽度统一；中间内容展示区作为功能页面重点修改区域。
- 后续页面的顶部横栏宽度与外层卡片结构统一以第二页 `FundList.vue` 为基准。
- 色彩方案（红涨绿跌 / 绿涨红跌）必须是用户可配置的，不得硬编码。已通过 Settings 页面和各页面顶栏统一实现。

## 4. 下一步

- 当前主线功能已完成真实链路收口，下一步以提交、PR 或发布整理为主。
- 若继续推进，优先级建议为：
- 1. 统一清理过期文档描述，避免 P0/P1 旧状态误导后续开发。
- 2. 为 Rust `EngineManager` 补充真正的自动化单元测试，避免 `cargo test` 长期为 0 tests。
- 3. 若进入发布准备，补齐 Tauri 正式图标资源，替换当前占位 `icon.png`。
- 4. 根据用户决定执行提交、建 PR 或继续功能迭代。
