# 分钟线数据获取与存储设计文档

## 1. 背景

- 当前系统已支持日线数据的获取、存储和聚合（周/月/季/年线）。
- 前端 `Analysis.vue` 已定义 9 种周期：分时、日K、5分、60分、120分、周K、月K、季K、年K。
- 缺少分钟线（1分、5分、60分、120分）的数据获取、存储和查询能力。
- akshare 支持 ETF/LOF 分钟线 API：`fund_etf_hist_min_em()` / `fund_lof_hist_min_em()`，period 参数支持 `'1'`、`'5'`、`'60'`，不支持 `'120'`。

## 2. 目标

- 新增分钟线数据获取能力（1 分、5 分、60 分钟）。
- 新增分钟线数据存储表，与日线表分离。
- 120 分钟线从 60 分钟线聚合，不单独存储。
- 支持初始批量注入和每日增量同步。
- 为后续前端图表展示和技术指标计算提供数据基础。

## 3. 方案决策

### 3.1 存储策略：新建 `minute_quote` 表

采用方案 B：新建独立的 `minute_quote` 表，与 `daily_quote` 表分离。

**理由：**
- 职责清晰，日线表不受影响。
- 字段类型正确（`datetime` vs `date`）。
- 查询性能好，分钟线和日线查询模式完全不同。
- 初始注入和增量同步可以独立控制。

### 3.2 数据来源策略

| 周期 | 来源 | 理由 |
|------|------|------|
| 1 分钟 | 直接获取 | 原始数据，盘中分析用 |
| 5 分钟 | 直接获取 | akshare 支持，历史更深（~30天） |
| 60 分钟 | 直接获取 | akshare 支持，历史更深 |
| 120 分钟 | 从 60 分钟聚合 | akshare 不支持，60→120 聚合简单可靠 |

**不采用纯 1 分钟线聚合方案的原因：**
- akshare 1 分钟线 API 仅返回约 5-10 个交易日，历史深度不足。
- 5 分钟和 60 分钟线可获取约 30 个交易日，数据质量更高。

### 3.3 初始注入天数

| 周期 | 天数 | 条数（1753 只基金） | 预估大小 |
|------|------|-------------------|---------|
| 1 分钟 | 5 天 | 210 万 | ~20 MB |
| 5 分钟 | 20 天 | 168 万 | ~16 MB |
| 60 分钟 | 60 天 | 42 万 | ~4 MB |
| 120 分钟 | 60 天（聚合） | 21 万 | ~2 MB |
| **合计** | | **442 万条** | **~42 MB** |

### 3.4 全量数据预估

| 周期 | akshare 最大历史 | 条数 | 预估大小 |
|------|----------------|------|---------|
| 1 分钟 | 10 天 | 421 万 | ~40 MB |
| 5 分钟 | 30 天 | 252 万 | ~24 MB |
| 60 分钟 | 30 天 | 21 万 | ~2 MB |
| 120 分钟 | 30 天（聚合） | 11 万 | ~1 MB |
| **合计** | | **705 万条** | **~67 MB** |

当前数据库 177MB，全量分钟线后约 244MB，SQLite 完全可控。

## 4. 数据库设计

### 4.1 新建 `minute_quote` 表

```sql
CREATE TABLE IF NOT EXISTS minute_quote (
    code TEXT NOT NULL,
    datetime TEXT NOT NULL,      -- 时间戳 "YYYY-MM-DD HH:MM:SS"
    period TEXT NOT NULL,        -- 周期标识: '1', '5', '60', '120'
    open REAL, close REAL, high REAL, low REAL,
    volume REAL, amount REAL,
    PRIMARY KEY (code, datetime, period),
    FOREIGN KEY (code) REFERENCES fund_info(code)
);

-- 查询优化索引
CREATE INDEX IF NOT EXISTS idx_minute_quote_code_period ON minute_quote(code, period, datetime);
```

**字段说明：**
- `datetime`: 完整时间戳，如 `"2024-01-15 09:31:00"`
- `period`: 周期标识，存储为字符串 `'1'`、`'5'`、`'60'`、`'120'`
- 主键为三元组 `(code, datetime, period)`，允许同一时刻存在不同周期的数据

### 4.2 120 分钟线聚合规则

从 60 分钟线聚合 120 分钟线的规则：
- 每个交易日分为两个 120 分钟段：
  - 上午段：09:30 - 11:30（含）
  - 下午段：13:00 - 15:00（含）
- 聚合逻辑：
  - `open` = 该段第一根 60 分钟线的 open
  - `high` = 该段所有 60 分钟线的 high 的最大值
  - `low` = 该段所有 60 分钟线的 low 的最小值
  - `close` = 该段最后一根 60 分钟线的 close
  - `volume` = 该段所有 60 分钟线的 volume 之和
  - `amount` = 该段所有 60 分钟线的 amount 之和
- `datetime` 存储为该 120 分钟段的起始时间

## 5. 数据获取层设计

### 5.1 `DataSource` 接口扩展

在 `src-python/engine/data/base.py` 的 `DataSource` 抽象类中新增：

```python
def fetch_minute_quotes(self, code: str, period: str) -> list[dict]:
    """获取分钟线数据
    Args:
        code: 基金代码
        period: 周期标识 '1', '5', '60'
    Returns:
        [{'datetime': 'YYYY-MM-DD HH:MM:SS', 'open': ..., 'close': ..., 
          'high': ..., 'low': ..., 'volume': ..., 'amount': ...}]
    """
```

### 5.2 `AkshareSource` 实现

在 `src-python/engine/data/akshare_source.py` 中实现：

```python
def fetch_minute_quotes(self, code: str, period: str) -> list[dict]:
    # 根据基金类型选择 API
    # ETF: ak.fund_etf_hist_min_em(symbol=code, period=period)
    # LOF: ak.fund_lof_hist_min_em(symbol=code, period=period)
    # 返回标准化格式
```

**注意事项：**
- akshare 分钟线 API 返回的列名包含 `时间`、`开盘`、`收盘`、`最高`、`最低`、`成交量`、`成交额`
- `时间` 格式为 `"2024-01-15 09:31:00"`，需标准化为 `"YYYY-MM-DD HH:MM:SS"`
- 需要添加 `time.sleep()` 避免请求过快被限流

## 6. 数据同步管道设计

### 6.1 `DataSyncPipeline` 扩展

在 `src-python/engine/sync.py` 中新增：

```python
def sync_minute_quotes_for_all(self, periods: list[str] = None):
    """同步所有基金的分钟线数据
    Args:
        periods: 需要同步的周期列表，默认 ['1', '5', '60']
    """
```

### 6.2 同步策略

**初始注入：**
- 遍历所有活跃基金
- 对每个基金分别获取 1 分、5 分、60 分钟线
- 获取完成后聚合 120 分钟线
- 批量写入 `minute_quote` 表

**每日增量同步：**
- 获取最近 N 天的分钟线（N 由 akshare API 限制决定）
- 使用 `UPSERT` 逻辑避免重复插入
- 重新聚合 120 分钟线

### 6.3 数据库操作方法

在 `Database` 类中新增：

```python
def upsert_minute_quotes(self, quotes: list[dict]):
    """批量插入或更新分钟线数据"""

def get_minute_quotes(self, code: str, period: str, start: str, end: str) -> list[dict]:
    """查询分钟线数据"""

def get_latest_minute_datetime(self, code: str, period: str) -> Optional[str]:
    """获取某只基金某周期的最新时间戳"""

def aggregate_120m_from_60m(self, code: str) -> list[dict]:
    """从 60 分钟线聚合 120 分钟线数据"""
```

## 7. 120 分钟聚合实现细节

### 7.1 聚合 SQL 逻辑

```sql
-- 伪代码，实际用 Python 实现
SELECT 
    code,
    MIN(datetime) as datetime,  -- 该段起始时间
    period,
    FIRST(open) as open,        -- 该段第一根的开盘价
    MAX(high) as high,          -- 该段最高价
    MIN(low) as low,            -- 该段最低价
    LAST(close) as close,       -- 该段最后一根的收盘价
    SUM(volume) as volume,      -- 该段总成交量
    SUM(amount) as amount       -- 该段总成交额
FROM minute_quote
WHERE period = '60'
GROUP BY code, date(datetime),  -- 按日期和时段分组
    CASE 
        WHEN strftime('%H:%M', datetime) < '11:30' THEN 'AM'
        ELSE 'PM'
    END
```

### 7.2 时段划分

A 股交易时段：
- 上午：09:30 - 11:30（120 分钟）
- 下午：13:00 - 15:00（120 分钟）

60 分钟线在每个交易日的分布：
- 09:30 - 10:30（第 1 根）
- 10:30 - 11:30（第 2 根）
- 13:00 - 14:00（第 3 根）
- 14:00 - 15:00（第 4 根）

所以每个交易日的 120 分钟线 = 上午 2 根 60 分钟线聚合 + 下午 2 根 60 分钟线聚合。

## 8. 前端数据接入

### 8.1 当前状态

`Analysis.vue` 当前**完全没有后端调用**，所有数据来自 `src/utils/analysisMock.ts` 硬编码：

```typescript
// Analysis.vue 第 419 行
const activeAnalysis = computed(() => (activeCode.value ? getAnalysisMockByCode(activeCode.value) : null))
```

### 8.2 前端期望的数据格式

```typescript
type AnalysisPeriod = {
  key: 'intraday' | 'day' | 'm5' | 'm60' | 'm120' | 'week' | 'month' | 'quarter' | 'year'
  label: string                   // "分时", "日K", "5分", "60分", "120分", ...
  summary: string                 // 周期摘要
  chartHeadline: string           // 图表标题
  chartSummary: string            // 图表说明
  priceAxis: string[]             // 价格刻度 ["4.06", "4.09", "4.12", "4.15"]
  timeAxis: string[]              // 时间刻度 ["09:30", "10:30", "11:30", "14:00", "15:00"]
  linePoints: number[]            // 折线图 Y 值（分时图用）
  avgLinePoints: number[]         // 均价线 Y 值（仅分时图）
  candles: number[][]             // K 线 [open, high, low, close][]
  volumes: number[]               // 成交量
  metrics: AnalysisMetric[]       // 技术指标卡
}
```

### 8.3 新增 JSON-RPC 方法

在 Python JSON-RPC 服务器中注册 `get_analysis_data` 方法：

```python
def get_analysis_data(code: str) -> dict:
    """获取指定基金的完整分析数据（所有周期）"""
```

返回格式：

```json
{
  "code": "510300",
  "name": "沪深300ETF",
  "market": "SH",
  "price": "4.123",
  "change": "+0.56%",
  "iopv": "4.118",
  "premium": "+0.12%",
  "riskLevel": "中等波动",
  "strategy": { ... },
  "periods": {
    "intraday": { "key": "intraday", "label": "分时", ... },
    "day": { "key": "day", "label": "日K", ... },
    "m5": { "key": "m5", "label": "5分", ... },
    "m60": { "key": "m60", "label": "60分", ... },
    "m120": { "key": "m120", "label": "120分", ... },
    "week": { "key": "week", "label": "周K", ... },
    "month": { "key": "month", "label": "月K", ... },
    "quarter": { "key": "quarter", "label": "季K", ... },
    "year": { "key": "year", "label": "年K", ... }
  }
}
```

### 8.4 后端数据转换逻辑

后端需要将数据库中的 OHLCV 数据转换为前端格式：

1. **K 线数据**：`daily_quote` / `minute_quote` → `candles`（`[open, high, low, close]` 数组）
2. **成交量**：直接映射到 `volumes`
3. **时间轴**：根据周期格式化为 `timeAxis`
4. **价格轴**：从 OHLC 数据计算 min/max，生成 4-5 个刻度
5. **分时图**：从当日 1 分钟线提取 `linePoints`（价格）和 `avgLinePoints`（均价线 = 累计成交额/累计成交量）
6. **技术指标**：调用 `TechnicalIndicators.compute_all(df)` 计算后转换为 `metrics` 格式

### 8.5 周期映射关系

| 前端 key | 后端数据来源 | 查询逻辑 |
|----------|------------|---------|
| `intraday` | `minute_quote` period='1' | 当日数据，按时间排序 |
| `day` | `daily_quote` | 最近 60 条 |
| `m5` | `minute_quote` period='5' | 最近 20 天 |
| `m60` | `minute_quote` period='60' | 最近 30 天 |
| `m120` | `minute_quote` period='120' | 最近 30 天（或从 60 分聚合） |
| `week` | `daily_quote` 聚合 | 按周分组 OHLCV |
| `month` | `daily_quote` 聚合 | 按月分组 OHLCV |
| `quarter` | `daily_quote` 聚合 | 按季分组 OHLCV |
| `year` | `daily_quote` 聚合 | 按年分组 OHLCV |

### 8.6 前端修改

`Analysis.vue` 需要在非 DEV 模式下调用真实后端：

```typescript
// 开发模式用 mock，生产模式用真实数据
const activeAnalysis = computed(async () => {
  if (!activeCode.value) return null
  if (import.meta.env.DEV) return getAnalysisMockByCode(activeCode.value)
  return await invoke_engine('get_analysis_data', { code: activeCode.value })
})
```

## 9. 错误处理与容错

### 8.1 API 限流

- akshare 有请求频率限制，每分钟线获取后需 `time.sleep(1)`
- 全量 1753 只基金 × 3 个周期 = 5259 次请求，约需 88 分钟
- 建议分批执行，支持断点续传

### 8.2 数据缺失

- 部分基金可能没有分钟线数据（如新上市、停牌）
- 获取失败时记录日志，不中断整体同步流程
- 可在 `fund_info` 表中增加 `has_minute_data` 字段标记

### 8.3 数据校验

- 分钟线数据的时间必须在交易时段内（09:30-11:30, 13:00-15:00）
- OHLC 值必须满足 `low <= open, close <= high`
- 异常数据应记录日志并跳过

## 10. 验证

### 10.1 Python 单元测试

- 测试 `fetch_minute_quotes` 返回格式正确
- 测试 `upsert_minute_quotes` 插入和更新逻辑
- 测试 `aggregate_120m_from_60m` 聚合结果正确
- 测试边界情况（空数据、停牌日、数据缺失）

### 10.2 数据量验证

- 初始注入后检查各周期数据条数是否符合预期
- 检查 120 分钟线条数是否为 60 分钟线的一半

### 10.3 性能验证

- 查询单只基金某周期 60 天数据应在 100ms 内返回
- 全量同步不应阻塞日线同步

### 10.4 前端接入验证

- `get_analysis_data` 返回的 `periods.m5`、`periods.m60`、`periods.m120` 数据格式与 `AnalysisPeriod` 类型完全匹配
- 前端切换周期后，图表、时间轴、价格轴、指标卡同步更新
- 分时图（`intraday`）正确渲染折线 + 均价线
- K 线图正确渲染蜡烛图

## 11. 下一步

- 基于本设计文档编写实现计划。
- 先实现数据获取层和数据库表结构。
- 再实现同步管道和 120 分钟聚合逻辑。
- 最后编写单元测试并验证。
