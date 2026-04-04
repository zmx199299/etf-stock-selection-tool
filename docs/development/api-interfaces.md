# FUNDFLOW 前后端接口开发文档

> 本文档是前后端对接的唯一参考来源，随开发进度持续更新。
>
> 最后更新：2026-04-04

---

## 目录

1. [架构总览](#1-架构总览)
2. [通信协议](#2-通信协议)
3. [接口清单](#3-接口清单)
4. [接口详细定义](#4-接口详细定义)
5. [后端能力现状](#5-后端能力现状)
6. [前端对接现状](#6-前端对接现状)
7. [已知问题与待办](#7-已知问题与待办)
8. [变更日志](#8-变更日志)

---

## 1. 架构总览

```
┌──────────────────┐     Tauri Command      ┌──────────────────┐     JSON-RPC        ┌──────────────────┐
│                  │    invoke_engine()      │                  │   stdin / stdout    │                  │
│   Vue 3 前端     │ ◄────────────────────► │   Rust 中间层     │ ◄────────────────► │   Python 引擎    │
│   (TypeScript)   │                        │   (Tauri 2)      │                     │   (数据+分析)    │
└──────────────────┘                        └──────────────────┘                     └──────────────────┘
```

**调用链路**：前端 `invoke('invoke_engine', { method, params })` → Rust `EngineManager.invoke()` → Python `JSONRPCServer.handle_request()` → 具体方法执行 → 原路返回结果。

**命名约定**：
- Python 端所有字段使用 **snake_case**（如 `current_price`、`premium_rate`）
- 前端 TypeScript 使用 **camelCase**（如 `currentPrice`、`premiumRate`）
- 前端负责做 snake_case → camelCase 的转换（参考 Dashboard 已有的 `toSharedFundCard`）

---

## 2. 通信协议

**协议**：JSON-RPC 2.0 over stdin/stdout

**请求格式**：
```json
{
  "jsonrpc": "2.0",
  "method": "方法名",
  "params": { ... },
  "id": 1
}
```

**成功响应**：
```json
{
  "jsonrpc": "2.0",
  "result": { ... },
  "id": 1
}
```

**错误响应**：
```json
{
  "jsonrpc": "2.0",
  "error": { "code": -32000, "message": "错误描述" },
  "id": 1
}
```

**标准错误码**：

| 错误码 | 含义 |
|---|---|
| -32700 | JSON 解析错误 |
| -32600 | 无效请求 |
| -32601 | 方法不存在 |
| -32000 | 服务端业务错误（通用） |

---

## 3. 接口清单

| 编号 | JSON-RPC 方法 | 消费页面 | 优先级 | 后端状态 | 前端状态 |
|---|---|---|---|---|---|
| API-01 | `ping` | — | P2 | ✅ 已实现 | 未使用 |
| API-02 | `get_engine_status` | — | P2 | ✅ 已实现（硬编码） | 未使用 |
| API-03 | `get_dashboard_signals` | Dashboard, Analysis | **P0** | ⚠️ 硬编码 Mock | ✅ invoke 已写，有 Mock 回退 |
| API-04 | `get_fund_list` | FundList | **P0** | ⚠️ 硬编码 Mock | ✅ invoke 已写，有 Mock 回退 |
| API-05 | `get_fund_analysis` | Analysis | **P1** | ❌ 未实现 | ❌ 纯前端 Mock 查表 |
| API-06 | `search_funds` | Analysis | **P1** | ❌ 未实现 | ❌ 纯前端 Mock 过滤 |
| API-07 | `get_screening_results` | （未来筛选页） | P2 | ⚠️ 硬编码 Mock | 未使用 |
| API-08 | `get_scoring_data` | （未来评分详情） | P2 | ⚠️ 硬编码 Mock | 未使用 |
| API-09 | `get_scheduler_data` | （未来调度页） | P2 | ⚠️ 硬编码 Mock | 未使用 |
| API-10 | `fetch_legal_tax_rates` | （设置页/费用） | P2 | ✅ 硬编码但准确 | 未使用 |

---

## 4. 接口详细定义

### API-03: `get_dashboard_signals`

> Dashboard 首页信号卡片 + Analysis 入口卡片条

**请求参数**：无

```json
{ "method": "get_dashboard_signals", "params": {} }
```

**返回值**：`DashboardSignal[]`

```python
# Python 端返回结构（snake_case）
[
    {
        "code": "512980",              # str  基金代码
        "name": "传媒ETF广发",          # str  基金名称
        "t_plus": "T+1",              # str  "T+0" | "T+1"
        "current_price": 0.985,        # float 当前价/最新价
        "change_pct": 1.85,            # float 涨跌幅百分比（如 1.85 表示 +1.85%）
        "buy_price": 0.980,            # float | null  建议买入价
        "sell_price": 0.987,           # float | null  建议卖出价
        "stop_loss": 0.955,            # float | null  止损价
        "latest_nav": 0.986,           # float | null  最新净值(IOPV)
        "nav_date": "2026-03-27",      # str | null    净值日期
        "premium_rate": -0.07,         # float | null  溢价率百分比
        "expected_profit": 61.40,      # float | null  预期收益金额
        "expected_profit_pct": 0.61,   # float | null  预期收益百分比
        "max_loss": 265.00,            # float | null  最大亏损金额
        "max_loss_pct": 2.65           # float | null  最大亏损百分比
    }
]
```

**数据来源（后端需串联）**：
- `code`, `name`, `t_plus` → `fund_info` 表
- `current_price`, `change_pct` → `daily_quote` 表最新记录 + 计算
- `latest_nav`, `nav_date`, `premium_rate` → `daily_quote` 表 nav 相关字段
- `buy_price`, `sell_price`, `stop_loss` → `scoring_result` 或 `screening_result` 表
- `expected_profit*`, `max_loss*` → 由 `CostCalculator` + 配置 budget 计算

**前端转换**：`toSharedFundCard()` 已存在于 `src/utils/dashboardSignals.ts`，将 snake_case → camelCase。

**注意**：当前后端 Mock 额外返回了 `buyable_shares` 字段，前端未使用。后续实现中如不需要可省略。

---

### API-04: `get_fund_list`

> FundList 基金列表页 — 全量活跃基金 + 行情 + 技术指标 + 评分

**请求参数**：无

```json
{ "method": "get_fund_list", "params": {} }
```

**返回值**：`FundListItem[]`

```python
# Python 端返回结构（snake_case）
[
    {
        "code": "510300",              # str   基金代码
        "name": "沪深300ETF",          # str   基金名称
        "prev_close": 4.100,           # float 昨收
        "open": 4.105,                 # float 开盘价
        "close": 4.123,                # float 现价（收盘/最新）
        "high": 4.150,                 # float 最高价
        "low": 4.080,                  # float 最低价
        "volatility": 0.0172,          # float 波动率 = (high-low)/low
        "macd": {                      # TechnicalValue
            "value": "金叉",           #   str   显示文本
            "signal": "bullish"        #   str   "bullish" | "bearish" | "neutral"
        },
        "rsi": { "value": "52", "signal": "neutral" },
        "boll": { "value": "中轨", "signal": "bullish" },
        "ma5": { "value": "上穿", "signal": "bullish" },
        "ma20": { "value": "粘合", "signal": "neutral" },
        "score": 9                     # int   综合评分 1-10
    }
]
```

**数据来源（后端需串联）**：
- `code`, `name` → `fund_info` 表
- `prev_close`, `open`, `close`, `high`, `low` → `daily_quote` 表最新记录
- `volatility` → 计算 `(high - low) / low`
- `macd`, `rsi`, `boll`, `ma5`, `ma20` → `TechnicalIndicators` 计算后的最新行数据，需转为文字描述+信号方向
- `score` → `Scorer` 的 `total_score` 映射到 1-10 分制

**前端转换**：当前 FundList.vue **缺少** snake_case → camelCase 转换层。需新增（参考 Dashboard 模式）。

**指标文字化规则**（后端需实现的转换逻辑）：

| 指标 | 看多(bullish) | 中性(neutral) | 看空(bearish) |
|---|---|---|---|
| MACD | DIF>DEA → "金叉"；hist>0 → "红柱" | DIF≈DEA → "粘合" | DIF<DEA → "死叉"；hist<0 → "绿柱" |
| RSI | RSI>60 → 具体数值 | 40≤RSI≤60 → 具体数值 | RSI<40 → 具体数值 |
| BOLL | close 靠近 lower → "下轨" | close 靠近 mid → "中轨" | close 靠近 upper → "上轨" |
| MA5 | MA5 > MA20 向上 → "上穿"/"多头" | 差值小 → "粘合" | MA5 < MA20 向下 → "下穿"/"空头" |
| MA20 | 斜率向上 → "向上" | 平坦 → "粘合" | 斜率向下 → "向下" |

**评分映射**（total_score 0-100 → score 1-10）：
```
score = max(1, min(10, round(total_score / 10)))
```

---

### API-05: `get_fund_analysis`

> Analysis 技术分析详情页 — 单支基金的完整多周期分析数据

**请求参数**：

```json
{
    "method": "get_fund_analysis",
    "params": {
        "code": "510300"
    }
}
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `code` | string | 是 | 基金代码 |

**返回值**：`FundAnalysis`

```python
{
    "code": "510300",
    "name": "沪深300ETF",
    "market": "SH",                    # str  "SH" | "SZ"
    "price": 4.123,                    # float 最新价
    "change_pct": 0.56,                # float 涨跌幅百分比
    "iopv": 4.118,                     # float | null 参考净值
    "premium_rate": 0.12,              # float | null 溢价率百分比
    "risk_level": "中等波动",           # str  "低波动" | "中等波动" | "高波动"

    "strategy": {
        "conclusion": "短期趋势偏多...",  # str  综合结论
        "buy_zone": "4.05 - 4.10",      # str  买入区间
        "sell_zone": "4.20 - 4.25",     # str  卖出区间
        "position": "建议30%仓位...",    # str  仓位建议
        "stop_loss": "跌破4.00止损...",  # str  止盈止损
        "holding_period": "3-5个交易日", # str  持有周期
        "risk_note": "注意..."          # str  风险提示
    },

    "periods": {
        "intraday": {
            "key": "intraday",
            "label": "分时",
            "summary": "...",              # str  周期摘要
            "chart_headline": "...",       # str  图旁解读标题
            "chart_summary": "...",        # str  图表说明
            "price_axis": ["4.10", "4.08", "4.06", "4.04"],  # str[]  Y轴刻度
            "time_axis": ["09:30", "10:30", "11:30", "13:30", "14:30"],  # str[]  X轴标签
            "line_points": [4.08, 4.07, ...],    # float[]  分时折线数据点
            "avg_line_points": [4.07, 4.07, ...], # float[]  均价线数据点
            "candles": [],                 # 分时无K线，为空数组
            "volumes": [1200, 1500, ...],  # float[]  成交量
            "metrics": [
                {
                    "label": "MACD",
                    "value": "金叉",
                    "summary": "DIF上穿DEA...",
                    "tone": "bullish"      # "bullish" | "neutral" | "bearish"
                }
                # ... 最多4个
            ]
        },
        "day": { ... },     # 日线
        "m5": { ... },      # 5分钟
        "m60": { ... },     # 60分钟
        "m120": { ... },    # 120分钟
        "week": { ... },    # 周线
        "month": { ... },   # 月线
        "quarter": { ... }, # 季线
        "year": { ... }     # 年线
    }
}
```

**周期数据通用说明**：
- `intraday`（分时）：`candles` 为空数组，使用 `line_points` + `avg_line_points` 画折线图
- 其他周期：`line_points` 和 `avg_line_points` 为空数组，使用 `candles` 画K线图
- `candles` 格式：`[[open, close, low, high], ...]`（注意：当前前端约定的顺序）
- `volumes`：与 `candles` 或 `line_points` 等长的成交量数组
- `metrics`：每个周期最多 4 个技术指标卡片

**数据来源（后端需串联）**：
- 基本信息 → `fund_info` 表 + `daily_quote` 最新
- `risk_level` → 基于 ATR14 / 波动率计算
- `strategy` → 基于 `Scorer` 评分结果 + 技术指标综合生成文字
- `periods` → 从 `AkshareSource.fetch_daily_quotes()` 获取不同周期数据 → `TechnicalIndicators.compute_all()` 计算 → 转为前端结构

**优先级说明**：此接口数据量大、逻辑复杂，建议分阶段实现：
1. **阶段一**：先实现 `day`（日线）周期，验证端到端链路
2. **阶段二**：扩展其他 K 线周期（week/month 等）
3. **阶段三**：实现 `intraday`（分时）和分钟级周期（需要分钟级数据源）

---

### API-06: `search_funds`

> Analysis 页面搜索框 — 基金代码/名称模糊搜索

**请求参数**：

```json
{
    "method": "search_funds",
    "params": {
        "keyword": "沪深"
    }
}
```

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 是 | 搜索关键字（代码或名称） |

**返回值**：`SearchResult[]`

```python
[
    {
        "code": "510300",
        "name": "沪深300ETF"
    },
    {
        "code": "510310",
        "name": "沪深300ETF易方达"
    }
]
```

**数据来源**：`fund_info` 表 `WHERE code LIKE '%keyword%' OR name LIKE '%keyword%'`，排除 `is_excluded=1` 的记录，最多返回 20 条。

---

### API-01: `ping`

> 引擎健康检查

**请求参数**：无

**返回值**：`"pong"`

**状态**：✅ 已实现，无需改动。

---

### API-02: `get_engine_status`

> 引擎运行状态

**请求参数**：无

**返回值**：
```python
{ "status": "running", "version": "1.0.0" }
```

**状态**：✅ 已实现，后续可扩展返回数据库同步时间等信息。

---

### API-10: `fetch_legal_tax_rates`

> 法定印花税率

**请求参数**：无

**返回值**：
```python
{
    "etf": { "stamp_duty": 0.0 },
    "lof": { "stamp_duty": 0.0 },
    "stock": { "stamp_duty": 0.5 }
}
```

**状态**：✅ 已实现，数据准确。

---

## 5. 后端能力现状

### 已实现的模块

| 模块 | 文件 | 能力 | 测试覆盖 |
|---|---|---|---|
| `AkshareSource` | `engine/data/akshare_source.py` | 从 akshare 获取 ETF/LOF 列表、日线行情、净值 | ✅ 集成测试（需联网） |
| `Database` | `engine/models/database.py` | SQLite 6 张表的 CRUD | ✅ 单元测试 |
| `TechnicalIndicators` | `engine/scoring/indicators.py` | MA/EMA/MACD/RSI/KDJ/WR/BOLL/ATR/OBV/量比 | ✅ 单元测试 |
| `Scorer` | `engine/scoring/scorer.py` | 四维评分 + 信号文字 + buy_value_score | ✅ 单元测试 |
| `PatternRecognizer` | `engine/scoring/patterns.py` | V 型反转识别 | ✅ 集成测试 |
| `CostCalculator` | `engine/scoring/calculator.py` | 买卖佣金 + 印花税 + 净利润 | ✅ 单元测试 |
| `ConfigManager` | `engine/utils/config.py` | JSON 配置文件读写 | ✅ 单元测试 |
| `JSONRPCServer` | `engine/server.py` | JSON-RPC 2.0 请求处理 | ✅ 单元测试 |

### 未串联的问题

**`server.py` 中的所有业务方法都是硬编码 Mock**，没有调用上述任何模块。需要做的核心工作是：

1. 在 server 启动时初始化 `Database` + `AkshareSource` + `TechnicalIndicators` + `Scorer`
2. 每个 RPC 方法改为调用真实模块而非返回硬编码数据
3. 新增数据同步流程（定时/手动从 akshare 拉取数据存入 SQLite）

---

## 6. 前端对接现状

### 调用方式

前端通过 Tauri Command 调用后端：

```typescript
// src/views/Dashboard.vue 等处
const result = await invoke('invoke_engine', {
    method: 'get_dashboard_signals',
    params: {}
})
```

### 各页面对接状态

| 页面 | Tauri invoke | Mock 回退 | snake→camel 转换 |
|---|---|---|---|
| Dashboard | ✅ 已写 | ✅ 有 | ✅ `toSharedFundCard()` |
| FundList | ✅ 已写 | ✅ 有 | ❌ **缺失** |
| Analysis | ❌ 未写 | ✅ 纯 Mock | ❌ 不适用 |
| Settings | — | — | — （纯本地） |

---

## 7. 已知问题与待办

### 待解决

| 编号 | 问题 | 优先级 | 说明 |
|---|---|---|---|
| ISSUE-01 | FundList 缺少 snake_case → camelCase 转换层 | P0 | 后端返回 snake_case 后，`prev_close` 等字段会匹配不上前端的 `prevClose` |
| ISSUE-02 | Analysis 页面无 Tauri invoke 路径 | P1 | 需要新增 `get_fund_analysis` 调用 + Mock 回退 |
| ISSUE-03 | server.py 业务方法全是硬编码 | P0 | 需要串联真实模块 |
| ISSUE-04 | 缺少数据同步流程 | P0 | 需要先有数据入库，接口才能返回真实数据 |
| ISSUE-05 | `get_dashboard_signals` 缺少 `change_pct` 字段 | P0 | 当前后端 Mock 没有返回此字段，前端需要 |
| ISSUE-06 | K线数据顺序约定 | P1 | 前端当前为 `[open, close, low, high]`，非标准 OHLC 顺序，需统一 |
| ISSUE-07 | Scorer 评分逻辑过于简单 | P2 | 当前固定返回 60 分，需要根据真实指标数据计算 |
| ISSUE-08 | 技术指标→文字描述的转换逻辑 | P1 | 后端需新增将数值指标转为"金叉/死叉/中轨"等文字的逻辑 |
| ISSUE-09 | 分钟级数据源 | P2 | `intraday`/`m5`/`m60`/`m120` 周期需要分钟级行情数据，akshare 是否支持待确认 |

### 实施优先级建议

```
第一步（P0 基础链路）：
  ├─ 数据同步流程：akshare → SQLite（fund_info + daily_quote）
  ├─ get_fund_list 接真实数据
  ├─ get_dashboard_signals 接真实数据
  └─ 前端 FundList 补 snake→camel 转换

第二步（P1 分析页）：
  ├─ 新增 get_fund_analysis 接口（先做日线周期）
  ├─ 新增 search_funds 接口
  ├─ 前端 Analysis 页补 invoke 调用
  └─ 技术指标文字化逻辑

第三步（P2 增强）：
  ├─ 扩展 get_fund_analysis 到更多周期
  ├─ 增强 Scorer 评分逻辑
  └─ 分钟级数据支持
```

---

## 8. 变更日志

| 日期 | 变更 |
|---|---|
| 2026-04-04 | 初始版本：梳理全部前端数据需求 + 后端已有能力，定义 6 个核心接口 |
