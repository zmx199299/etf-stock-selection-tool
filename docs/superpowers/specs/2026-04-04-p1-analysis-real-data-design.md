# P1 Analysis 九周期真实化设计文档

## 目标

将第三页 `Analysis.vue` 从纯前端 Mock 页面推进为**真实可用**的技术分析页面。

本阶段目标不是“只做最小演示”，而是让以下能力具备真实数据支撑：

- 真实基金搜索 `search_funds`
- 真实技术分析详情 `get_fund_analysis`
- 九周期全部具备真实数据来源：
  - `intraday`
  - `day`
  - `m5`
  - `m60`
  - `m120`
  - `week`
  - `month`
  - `quarter`
  - `year`

## 当前现状

### 前端

- `Analysis.vue` 已具备成熟的九周期展示壳层、摘要卡、策略卡、图表区、指标卡、tooltip 交互。
- 当前数据全部来自 `src/utils/analysisMock.ts`。
- 页面结构已经稳定，因此本阶段应尽量**保持 UI 结构不动，只替换数据来源**。

### 后端

- 已具备：
  - `AkshareSource.fetch_fund_list()`
  - `AkshareSource.fetch_daily_quotes()`
  - `AkshareSource.fetch_nav()`
  - `TechnicalIndicators`
  - `Scorer`
  - `DataSyncPipeline`
- 已确认 `AKShare` 还支持：
  - `fund_etf_hist_min_em`
  - `fund_lof_hist_min_em`
- 当前项目代码尚未封装分钟级抓取能力。

## 数据源真实性结论

### 已验证能力

AKShare 对 ETF / LOF 可提供以下真实行情能力：

- 日线 / 周线 / 月线历史行情
- 1 分钟行情
- 5 分钟行情
- 15 分钟行情
- 30 分钟行情
- 60 分钟行情

### 已知限制

- 1 分钟数据仅能获取**近 5 个交易日**，且通常不复权
- AKShare **没有原生 120 分钟周期**
- 因此 `m120` 必须在本项目中由 `m60` 聚合生成
- `quarter` / `year` 也不应依赖额外外部接口，而应由 `month` 聚合生成，避免口径分裂

## 设计选择

### 选定方案：单接口统一真实化

保持单一主接口：

- `search_funds(keyword)`
- `get_fund_analysis(code)`

由后端统一负责：

- 数据获取
- 周期聚合
- 技术指标计算
- 指标文字化
- 策略文案生成
- 前端结构映射

### 不采用的方案

#### 1. 多接口按周期拆分

不采用原因：

- 前端当前结构是“单基金详情 + 本地切换周期”
- 按周期拆接口会导致切换周期频繁请求
- 增加页面复杂度与加载抖动

#### 2. 前端自己做聚合和指标转换

不采用原因：

- 会把金融分析逻辑分散到前端
- 造成后端与前端口径不统一
- 不利于后续真实可用目标

## 周期映射设计

### 直接来自 AKShare 的周期

- `intraday` -> `period='1'`
- `m5` -> `period='5'`
- `m60` -> `period='60'`
- `day` -> 日线
- `week` -> 周线
- `month` -> 月线

### 项目内聚合生成的周期

- `m120` -> 基于 `m60` 两根一组聚合
- `quarter` -> 基于 `month` 三根一组聚合
- `year` -> 基于 `month` 十二根一组聚合

### 聚合规则

聚合 K 线统一规则：

- `open` = 分组第一根的开盘价
- `close` = 分组最后一根的收盘价
- `high` = 分组内最高价最大值
- `low` = 分组内最低价最小值
- `volume` = 分组内成交量求和
- `amount` = 分组内成交额求和
- 时间标签采用分组最后一根时间，作为前端显示时间轴

## 后端模块拆分

为避免把复杂逻辑继续堆进 `server.py`，本阶段新增以下模块：

### 1. `src-python/engine/data/akshare_source.py`

新增分钟级抓取能力：

- `fetch_etf_minute_quotes()` 或统一的分钟级抓取方法
- 能根据基金类型（ETF / LOF）调用对应 AKShare 接口

职责：

- 只负责从外部获取原始数据
- 不负责周期聚合
- 不负责前端结构转换

### 2. `src-python/engine/services/aggregation.py`

职责：

- `m60 -> m120` 聚合
- `month -> quarter` 聚合
- `month -> year` 聚合
- 保持聚合逻辑独立、可测试

### 3. `src-python/engine/services/period_builder.py`

职责：

- 将原始行情 + 指标计算结果转换为前端 `periods` 结构
- 生成：
  - `price_axis`
  - `time_axis`
  - `line_points`
  - `avg_line_points`
  - `candles`
  - `volumes`
  - `metrics`

### 4. `src-python/engine/services/analysis_service.py`

职责：

- 实现 `search_funds`
- 实现 `get_fund_analysis`
- 汇总基金基础信息、净值、溢价率、风险等级、策略建议
- 调用 `period_builder` 生成九周期结果

### 5. `src-python/engine/server.py`

职责：

- 只做 JSON-RPC 方法注册
- 将 `search_funds` / `get_fund_analysis` 绑定到 `AnalysisService`

## `get_fund_analysis` 返回结构策略

保持与当前前端结构尽可能一致，减少前端重构。

### 字段策略

- 后端保持 snake_case
- 前端新增一个 Analysis 专用转换层，将真实返回映射到当前 `Analysis.vue` 需要的 camelCase 结构

### 基础信息

后端返回：

- `code`
- `name`
- `market`
- `price`
- `change_pct`
- `iopv`
- `premium_rate`
- `risk_level`

前端转换为当前展示字段：

- `price` -> 字符串显示值
- `change_pct` -> `+0.56%` / `-1.20%`
- `premium_rate` -> 百分比字符串

### 策略建议

本阶段允许策略文案采用“真实数据驱动 + 模板生成”的方式，而不是一次性做复杂智能投顾。

包括：

- `conclusion`
- `buy_zone`
- `sell_zone`
- `position`
- `stop_loss`
- `holding_period`
- `risk_note`

策略生成依据：

- 日线最新价
- 周期趋势方向
- `Scorer` 评分结果
- ATR / 波动率
- 支撑阻力近似区间

## `search_funds` 设计

### 输入

- `keyword`

### 查询来源

- `fund_info` 表

### 规则

- 匹配 `code` 或 `name`
- 排除 `is_excluded = 1`
- 最多返回 20 条
- 优先返回代码前缀命中的结果，再返回名称模糊命中结果

### 返回

- `code`
- `name`

## 前端接入设计

### 保持不变的部分

- `Analysis.vue` 页面布局
- 九周期切换 UI
- tooltip 与图表展示壳层
- 入口卡片布局

### 新增前端数据层

建议新增：

- `src/utils/analysisApi.ts`

职责：

- 调用 `invoke_engine`
- 调用 `search_funds`
- 调用 `get_fund_analysis`
- 将后端真实结构转换为前端当前 `Analysis.vue` 使用的结构
- 在失败时保留当前 mock 回退

### 替换点

- 替换 `searchAnalysisCandidates()` 的调用路径
- 替换 `getAnalysisMockByCode()` 的调用路径
- 保留 `analysisMock.ts` 作为临时兜底，不立即删除

## 异常与降级策略

### 搜索失败

- 前端回退到当前 mock 搜索

### 单基金分析失败

- 前端回退到当前 mock 详情
- 但需要保留明确日志，便于继续联调

### 周期级别数据不足

本阶段后端不应伪造周期数据。

规则：

- 能算则返回真实结果
- 数据不足则返回空数组和清晰摘要说明
- 前端展示“该周期暂无足够真实数据”而不是静默伪造

## 测试设计

### Python 测试

新增测试类别：

- AKShare 分钟级抓取适配测试
- ETF / LOF 分钟级接口选择测试
- `m120` 聚合测试
- `quarter` 聚合测试
- `year` 聚合测试
- `search_funds` 测试
- `get_fund_analysis` 服务测试
- `server.py` RPC 注册与返回结构测试

### 前端测试

新增测试类别：

- Analysis 搜索调用真实接口测试
- Analysis 详情真实加载测试
- 九周期切换兼容真实结构测试
- 回退到 mock 的失败兜底测试

## 范围边界

本阶段做：

- 九周期真实数据打通
- `search_funds`
- `get_fund_analysis`
- 前端 Analysis 页真实接入

本阶段不做：

- ECharts 替换
- 更复杂的 AI 解读文案
- 更高级的多因子策略优化
- Rust 中间层结构重构

## 成功标准

完成后应满足：

- 用户在 Analysis 顶部搜索能查到真实基金
- 用户点入基金后，九个周期都能展示真实数据或明确说明该周期暂无足够真实数据
- 前端页面结构和交互不退化
- Python 测试、前端测试、构建验证均通过
- 页面不再只是 demo，而是具备真实查询与真实分析能力
