# ETF 智能分析系统 - AI 当前状态指针

**最后更新**: 2026-04-06 00:59 (UTC+8)

## 1. 当前阶段

当前阶段为 **GitHub 三平台自动发布已打通，并完成 `v0.0.5` 正式发布**。应用现在会在启动时先执行一次数据同步，Windows 安装包文件名也已去掉 `en-US` 后缀。

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

### Page 5 — 评分详情 (Scoring) ✅ 新完成真实化
- `Scoring.vue` 页面已彻底移除假数据 `mockScoringData`。
- **技术打分**：已对接真实后端 `AnalysisService.get_scoring_data`，获取并展示 `trend_score`, `momentum_score`, `volatility_score`, `volume_score` 及信号（目前后端 Scorer 采用基础策略或固定分值，保留算法升级空间）。
- **交易建议**：后端动态计算建议买入量（预设按10000元基础投资）、预估费用、止损价（95%）和止盈价（110%）。
- **交互与测试**：新增 `isLoading` 和 `errorMsg`，`Scoring.spec.ts`、Python的 `test_analysis_service.py` 均更新了对真实 `invoke_engine` 路由和策略逻辑的断言。

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
- Tauri 图标资源已收口：`src-tauri/icons/` 下包含 16x16 至 512x512 多尺寸 PNG 及 `icon.png`，K 线蜡烛图标（commit `f7a3eb5`）。
- 测试基线：前端 11 个测试文件，112 个测试用例全部通过；Python 端 **65 个测试通过**（2 个外部依赖测试按环境跳过）；Rust 端 `cargo test` **10 个测试全部通过**（从 5 个新增到 10 个，覆盖 JSON-RPC 请求序列化、响应解析、错误传播、req_id 递增、复杂参数往返）。
- TypeScript 类型检查 + Vite 构建通过。

### 发布与版本统一 (2026-04-05 深夜 / 2026-04-06 凌晨)

- 发布版本已统一到 `v0.0.5`
- 已同步更新：
  - `package.json`
  - `package-lock.json`
  - `src-tauri/tauri.conf.json`
  - `src-tauri/Cargo.toml`
  - `src-tauri/Cargo.lock`
- 系统设置页版本显示继续直接读取 `package.json`，当前展示为 `v0.0.5 预览版`
- Windows 打包缺失图标问题已修复：
  - 新增 `src-tauri/icons/icon.ico`
  - `bundle.icon` 已包含 `icons/icon.ico`
- 新增版本一致性保护测试，校验：
  - `package.json` / `package-lock.json` / `tauri.conf.json` / `Cargo.toml` 版本一致
  - Windows bundler 所需 `icons/icon.ico` 已登记到 Tauri 配置
- 启动同步能力已接入：
  - `src/main.ts` 会在挂载 Vue 应用前先执行 `ensureStartupSync()`
  - Dashboard / FundList 页面保留页面级兜底
  - 同步失败会提示“启动同步失败，请注意核对当前数据状态”
  - 同步进行中不会误显示空状态
- Windows MSI release 上传前会去掉 `_en-US` 后缀
- `Release` workflow run `24006001647` 已全部成功
- 正式发布地址：`https://github.com/zmx199299/etf-stock-selection-tool/releases/tag/v0.0.5`
- 当前发布产物：
  - Linux：RPM / DEB / AppImage
  - macOS：x64 DMG / aarch64 DMG
  - Windows：x64 MSI（文件名已不含 `en-US`）

### 全量库严格全量 + 标记隔离 (2026-04-05 下午)

**问题**：约 22 只 LOF 在新浪分类页 `最新价=0.0`、`成交量=0`，无场内交易行情。`sync_all.py` 遇到空行情即中断导入。

**方案**：严格全量 + 标记隔离（用户选择方案 B）

**实现**（7 个提交）：

| 提交 | 说明 |
|------|------|
| `b96605a` | 数据库层：`has_market_data INTEGER DEFAULT 1` + `get_all_funds_with_market_data()` + `update_has_market_data()` + 输入验证 + `update_daily_quote_nav_and_premium()` |
| `600981e` | 种子同步层：根据新浪分类页成交量/最新价标记 `has_market_data` |
| `bd1715d` | 重构：提取 `classify_invest_type()` 和 `classify_t_plus()` 为模块级纯函数 |
| `bf3dbe7` | 同步脚本：跳过无行情基金 + 报告统计 |
| `7f7ea0d` | 修复：封装 `_update_nav` 为公开方法 + 净值缺失降级为 warning |
| `6a99bab` | 修复：`DataSyncPipeline` 改用 `get_all_funds_with_market_data()` |
| `43860d0` | 文档：更新 AI 状态 |

**代码质量审阅发现并修复的问题**：
- 私有方法调用 `_classify_invest_type()` / `_classify_t_plus()` → 提取为模块级纯函数
- 裸 SQL 直接操作 `db.conn` → 封装为 `update_daily_quote_nav_and_premium()`
- `_update_nav()` 私有方法被脚本层调用 → 封装为公开方法
- 缺少净值快照抛 `RuntimeError` → 降级为 warning + continue
- `DataSyncPipeline` 不尊重 `has_market_data` → 改用 `get_all_funds_with_market_data()`

**新增测试**：6 个（database 3 个、seed_sync 1 个、sync_all 2 个）
**测试总数**：49 → 65 passed, 2 skipped

**规格文档**：`docs/superpowers/specs/2026-04-05-full-market-db-has-market-data-design.md`
**实施计划**：`docs/superpowers/plans/2026-04-05-full-market-has-market-data-plan.md`

### 文档清理完成 (2026-04-05)

- `docs/development/human/01_phase1_python_engine.md` — 已添加历史快照免责声明
- `docs/development/human/02_phase2_rust_integration.md` — 已添加历史快照免责声明
- `docs/development/human/03_phase3_frontend.md` — 已添加历史快照免责声明
- `docs/development/ai/` 下四份历史快照文件已有免责声明，维持现状

### Rust 单元测试补齐 (2026-04-05)

- 从 5 个测试增加到 10 个测试，全部通过
- 新增测试：
  - `test_invoke_with_echo_process` — 正常 JSON-RPC 请求-响应解析
  - `test_invoke_with_error_response` — Python 端错误正确透传
  - `test_invoke_with_null_result` — result 为 null 时返回错误
  - `test_req_id_increments` — 每次 invoke 后 req_id 递增
  - `test_invoke_with_complex_params` — 复杂嵌套 JSON 参数正确往返
- 清理了 `engine.rs` 中未使用的导入（`ChildStdin`、`ChildStdout`、`Arc`、`Mutex`）

## 3. 当前约束

- 继续遵循 Mock 优先，不在用户确认前擅自推进真实数据联动或深度交互扩展。
- 后续页面统一遵循三区结构：左侧导航栏固定不改；顶部横栏风格与宽度统一；中间内容展示区作为功能页面重点修改区域。
- 后续页面的顶部横栏宽度与外层卡片结构统一以第二页 `FundList.vue` 为基准。
- 色彩方案（红涨绿跌 / 绿涨红跌）必须是用户可配置的，不得硬编码。已通过 Settings 页面和各页面顶栏统一实现。

## 4. 已完成项回顾

- [x] 全量库严格全量 + 标记隔离 — 7 个提交，65 个 Python 测试全绿
- [x] 全量数据导入验证 — 1,753 只基金，1,742,865 条日线，1,749 条净值
- [x] 清理过期文档 — 三份 human 版 Phase 文档已添加历史快照免责声明
- [x] Rust 单元测试补齐 — 10 个测试全部通过
- [x] Tauri 图标 — K 线蜡烛图标已替换（commit `f7a3eb5`）
- [x] GitHub Actions 自动发布 — `v0.0.5` 已完成 Linux / macOS / Windows 三平台正式发布
- [x] 版本统一 — 前端显示版本、package、Tauri、Cargo、tag 已统一到 `v0.0.5`
- [x] 启动同步 — 应用挂载前先执行一次 `sync_data`
- [x] Windows 安装包命名 — Release 中的 MSI 已去掉 `_en-US`

## 5. 下一步

- 继续推进业务功能，而不是发布基础设施
- 优先项可回到：分钟线按需实时获取、前端真实联动与缓存策略
- 后续每次发版都必须继续遵守：先同步版本号，再推送对应 tag，再检查三平台 release 产物是否齐全
