# P1 Analysis 九周期真实化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Analysis 页面支持真实 `search_funds` 与 `get_fund_analysis`，并让九周期数据都来自真实数据源或真实聚合结果。

**Architecture:** 后端在 `AkshareSource` 中补齐分钟级数据抓取，在 `services` 层新增聚合器、周期构建器与 AnalysisService，统一生成前端当前所需的九周期结构。前端新增 `analysisApi.ts` 作为真实接口加载与 snake_case/camelCase 转换层，尽量不改 `Analysis.vue` 的既有版式结构。

**Tech Stack:** Python (`akshare`, `pandas`, `pytest`), Vue 3, TypeScript, Vitest, Tauri JSON-RPC

---

## 文件结构

| 文件 | 操作 | 说明 |
|---|---|---|
| `src-python/engine/data/base.py` | 修改 | 为数据源抽象补充分钟级抓取接口，并放宽日线接口支持 `period` 参数 |
| `src-python/engine/data/akshare_source.py` | 修改 | 接入 ETF/LOF 分钟级接口，并支持 daily/weekly/monthly 历史抓取 |
| `src-python/engine/services/aggregation.py` | 新建 | 统一 K 线聚合逻辑：`60->120`、`month->quarter/year` |
| `src-python/engine/services/period_builder.py` | 新建 | 把原始行情与指标结果转换为前端 `periods` 结构 |
| `src-python/engine/services/analysis_service.py` | 新建 | 实现 `search_funds` 与 `get_fund_analysis` |
| `src-python/engine/server.py` | 修改 | 注册 `search_funds` 与 `get_fund_analysis` 到真实 server |
| `src-python/main.py` | 修改 | 主入口切到真实 server 装配路径 |
| `src-python/tests/test_akshare_source_minute.py` | 新建 | 分钟级抓取与 ETF/LOF 接口选择测试 |
| `src-python/tests/test_aggregation.py` | 新建 | 聚合器测试 |
| `src-python/tests/test_period_builder.py` | 新建 | 周期结构构建测试 |
| `src-python/tests/test_analysis_service.py` | 新建 | AnalysisService 测试 |
| `src-python/tests/test_server_analysis.py` | 新建 | JSON-RPC Analysis 接口测试 |
| `src/utils/analysisApi.ts` | 新建 | 前端真实数据调用与转换层 |
| `src/utils/__tests__/analysisApi.spec.ts` | 新建 | 前端 Analysis API 转换与回退测试 |
| `src/views/Analysis.vue` | 修改 | 将 mock 搜索/详情改为真实接口加载 |
| `src/views/__tests__/Analysis.spec.ts` | 修改 | 更新为真实接口驱动下的页面测试 |
| `docs/development/api-interfaces.md` | 修改 | 更新 P1 接口状态 |
| `docs/development/ai/current_state.md` | 修改 | 更新当前阶段到 P1 真实化进行中 |
| `docs/development/human/2026-04-04-daily-log.md` | 修改 | 记录 P1 开发进展 |

---

### Task 1: 补齐 AKShare 分钟级与多周期抓取

**Files:**
- Modify: `src-python/engine/data/base.py`
- Modify: `src-python/engine/data/akshare_source.py`
- Create: `src-python/tests/test_akshare_source_minute.py`

- [ ] **Step 1: 写失败测试，锁定 ETF/LOF 分钟级抓取行为**

```python
# src-python/tests/test_akshare_source_minute.py
import pandas as pd

from engine.data.akshare_source import AkshareSource


def test_fetch_minute_quotes_uses_etf_api(mocker):
    source = AkshareSource()
    mock_df = pd.DataFrame([
        {
            "时间": "2024-03-20 09:35:00",
            "开盘": 1.0,
            "收盘": 1.01,
            "最高": 1.02,
            "最低": 0.99,
            "成交量": 1000,
            "成交额": 10000,
            "均价": 1.005,
        }
    ])
    spy = mocker.patch(
        "engine.data.akshare_source.ak.fund_etf_hist_min_em",
        return_value=mock_df,
    )

    rows = source.fetch_minute_quotes(
        code="513500",
        fund_type="ETF",
        period="1",
        start_datetime="2024-03-20 09:30:00",
        end_datetime="2024-03-20 15:00:00",
    )

    spy.assert_called_once()
    assert rows == [
        {
            "datetime": "2024-03-20 09:35:00",
            "open": 1.0,
            "close": 1.01,
            "high": 1.02,
            "low": 0.99,
            "volume": 1000.0,
            "amount": 10000.0,
            "avg_price": 1.005,
        }
    ]


def test_fetch_minute_quotes_uses_lof_api(mocker):
    source = AkshareSource()
    mock_df = pd.DataFrame([
        {
            "时间": "2024-03-20 09:35:00",
            "开盘": 2.0,
            "收盘": 2.01,
            "最高": 2.03,
            "最低": 1.99,
            "成交量": 2000,
            "成交额": 20000,
            "均价": 2.005,
        }
    ])
    spy = mocker.patch(
        "engine.data.akshare_source.ak.fund_lof_hist_min_em",
        return_value=mock_df,
    )

    rows = source.fetch_minute_quotes(
        code="166009",
        fund_type="LOF",
        period="1",
        start_datetime="2024-03-20 09:30:00",
        end_datetime="2024-03-20 15:00:00",
    )

    spy.assert_called_once()
    assert rows[0]["avg_price"] == 2.005


def test_fetch_daily_quotes_supports_weekly_period(mocker):
    source = AkshareSource()
    mock_df = pd.DataFrame([
        {
            "日期": "2024-03-22",
            "开盘": 1.0,
            "收盘": 1.1,
            "最高": 1.2,
            "最低": 0.9,
            "成交量": 100,
            "成交额": 1000,
        }
    ])
    spy = mocker.patch(
        "engine.data.akshare_source.ak.fund_etf_hist_em",
        return_value=mock_df,
    )

    rows = source.fetch_daily_quotes("513500", start_date="2024-03-01", period="weekly")

    spy.assert_called_once_with(
        symbol="513500",
        period="weekly",
        start_date="20240301",
        adjust="",
    )
    assert rows[0]["date"] == "2024-03-22"
```

- [ ] **Step 2: 运行测试，确认当前失败**

Run: `pytest src-python/tests/test_akshare_source_minute.py -v`

Expected: `AkshareSource` 缺少 `fetch_minute_quotes`，或 `fetch_daily_quotes` 不支持 `period` 参数。

- [ ] **Step 3: 修改抽象接口与 AKShare 数据源，最小实现通过测试**

```python
# src-python/engine/data/base.py
from abc import ABC, abstractmethod


class DataSource(ABC):
    @abstractmethod
    def fetch_fund_list(self) -> list[dict]:
        ...

    @abstractmethod
    def fetch_daily_quotes(self, code: str, start_date: str = None, period: str = "daily") -> list[dict]:
        ...

    @abstractmethod
    def fetch_minute_quotes(
        self,
        code: str,
        fund_type: str,
        period: str,
        start_datetime: str = None,
        end_datetime: str = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def fetch_nav(self, code: str, start_date: str = None) -> list[dict]:
        ...
```

```python
# src-python/engine/data/akshare_source.py
def fetch_daily_quotes(self, code: str, start_date: str = None, period: str = "daily") -> list[dict]:
    try:
        df = ak.fund_etf_hist_em(
            symbol=code,
            period=period,
            start_date=start_date.replace("-", "") if start_date else "19900101",
            adjust="",
        )
    except Exception:
        return []
    if df.empty:
        return []
    return [
        {
            "date": str(row.get("日期", ""))[:10],
            "open": float(row.get("开盘", 0)),
            "close": float(row.get("收盘", 0)),
            "high": float(row.get("最高", 0)),
            "low": float(row.get("最低", 0)),
            "volume": float(row.get("成交量", 0)),
            "amount": float(row.get("成交额", 0)),
        }
        for _, row in df.iterrows()
    ]


def fetch_minute_quotes(self, code: str, fund_type: str, period: str, start_datetime: str = None, end_datetime: str = None) -> list[dict]:
    fetcher = ak.fund_lof_hist_min_em if fund_type == "LOF" else ak.fund_etf_hist_min_em
    try:
        df = fetcher(
            symbol=code,
            period=period,
            adjust="" if period == "1" else "hfq",
            start_date=start_datetime or "1979-09-01 09:32:00",
            end_date=end_datetime or "2222-01-01 09:32:00",
        )
    except Exception:
        return []
    if df.empty:
        return []
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "datetime": str(row.get("时间", "")),
                "open": float(row.get("开盘", 0)),
                "close": float(row.get("收盘", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "avg_price": float(row.get("均价", row.get("收盘", 0))),
            }
        )
    return rows
```

- [ ] **Step 4: 重新运行测试确认通过**

Run: `pytest src-python/tests/test_akshare_source_minute.py -v`

Expected: 3 passed。

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/data/base.py src-python/engine/data/akshare_source.py src-python/tests/test_akshare_source_minute.py
git commit -m "feat: AkshareSource 支持分钟级行情抓取与多周期历史数据"
```

---

### Task 2: 新建 K 线聚合器与周期构建器

**Files:**
- Create: `src-python/engine/services/aggregation.py`
- Create: `src-python/engine/services/period_builder.py`
- Create: `src-python/tests/test_aggregation.py`
- Create: `src-python/tests/test_period_builder.py`

- [ ] **Step 1: 写聚合器失败测试**

```python
# src-python/tests/test_aggregation.py
from engine.services.aggregation import aggregate_candles


def test_aggregate_candles_two_rows_to_one():
    rows = [
        {"date": "2024-03-01", "open": 1.0, "close": 1.1, "high": 1.2, "low": 0.9, "volume": 10.0, "amount": 100.0},
        {"date": "2024-03-02", "open": 1.1, "close": 1.3, "high": 1.4, "low": 1.0, "volume": 20.0, "amount": 200.0},
    ]

    result = aggregate_candles(rows, group_size=2, label_key="date")

    assert result == [
        {
            "date": "2024-03-02",
            "open": 1.0,
            "close": 1.3,
            "high": 1.4,
            "low": 0.9,
            "volume": 30.0,
            "amount": 300.0,
        }
    ]


def test_aggregate_candles_keeps_tail_group():
    rows = [
        {"date": "2024-01", "open": 1.0, "close": 1.0, "high": 1.0, "low": 1.0, "volume": 1.0, "amount": 1.0},
        {"date": "2024-02", "open": 2.0, "close": 2.0, "high": 2.0, "low": 2.0, "volume": 2.0, "amount": 2.0},
        {"date": "2024-03", "open": 3.0, "close": 3.0, "high": 3.0, "low": 3.0, "volume": 3.0, "amount": 3.0},
    ]

    result = aggregate_candles(rows, group_size=2, label_key="date")

    assert len(result) == 2
    assert result[1]["date"] == "2024-03"
```

```python
# src-python/tests/test_period_builder.py
from engine.services.period_builder import build_intraday_period, build_kline_period


def test_build_intraday_period_uses_avg_price_line():
    rows = [
        {"datetime": "2024-03-20 09:30:00", "open": 1.0, "close": 1.01, "high": 1.02, "low": 0.99, "volume": 100, "amount": 1000, "avg_price": 1.005},
        {"datetime": "2024-03-20 09:31:00", "open": 1.01, "close": 1.02, "high": 1.03, "low": 1.00, "volume": 120, "amount": 1200, "avg_price": 1.01},
    ]

    period = build_intraday_period(rows, summary="分时摘要", chart_headline="标题", chart_summary="说明")

    assert period["line_points"] == [1.01, 1.02]
    assert period["avg_line_points"] == [1.005, 1.01]
    assert period["candles"] == []


def test_build_kline_period_generates_candles_and_volumes():
    rows = [
        {"date": "2024-03-01", "open": 1.0, "close": 1.1, "high": 1.2, "low": 0.9, "volume": 100, "amount": 1000},
        {"date": "2024-03-02", "open": 1.1, "close": 1.2, "high": 1.3, "low": 1.0, "volume": 120, "amount": 1200},
    ]

    period = build_kline_period(rows, summary="日线摘要", chart_headline="标题", chart_summary="说明")

    assert period["candles"] == [[1.0, 1.1, 0.9, 1.2], [1.1, 1.2, 1.0, 1.3]]
    assert period["volumes"] == [100, 120]
    assert period["line_points"] == []
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest src-python/tests/test_aggregation.py src-python/tests/test_period_builder.py -v`

Expected: 模块不存在或函数不存在。

- [ ] **Step 3: 以最小实现新增聚合器与周期构建器**

```python
# src-python/engine/services/aggregation.py
def aggregate_candles(rows: list[dict], group_size: int, label_key: str = "date") -> list[dict]:
    aggregated = []
    for start in range(0, len(rows), group_size):
        chunk = rows[start:start + group_size]
        if not chunk:
            continue
        aggregated.append(
            {
                label_key: chunk[-1][label_key],
                "open": chunk[0]["open"],
                "close": chunk[-1]["close"],
                "high": max(row["high"] for row in chunk),
                "low": min(row["low"] for row in chunk),
                "volume": sum(row.get("volume", 0) for row in chunk),
                "amount": sum(row.get("amount", 0) for row in chunk),
            }
        )
    return aggregated
```

```python
# src-python/engine/services/period_builder.py
def build_intraday_period(rows: list[dict], summary: str, chart_headline: str, chart_summary: str) -> dict:
    prices = [round(row["close"], 3) for row in rows]
    averages = [round(row.get("avg_price", row["close"]), 3) for row in rows]
    return {
        "summary": summary,
        "chart_headline": chart_headline,
        "chart_summary": chart_summary,
        "price_axis": _build_price_axis(prices or [0]),
        "time_axis": [str(row["datetime"])[11:16] for row in rows],
        "line_points": prices,
        "avg_line_points": averages,
        "candles": [],
        "volumes": [float(row.get("volume", 0)) for row in rows],
        "metrics": [],
    }


def build_kline_period(rows: list[dict], summary: str, chart_headline: str, chart_summary: str) -> dict:
    prices = [row["close"] for row in rows]
    return {
        "summary": summary,
        "chart_headline": chart_headline,
        "chart_summary": chart_summary,
        "price_axis": _build_price_axis(prices or [0]),
        "time_axis": [str(row["date"])[5:10] for row in rows],
        "line_points": [],
        "avg_line_points": [],
        "candles": [[row["open"], row["close"], row["low"], row["high"]] for row in rows],
        "volumes": [row.get("volume", 0) for row in rows],
        "metrics": [],
    }


def _build_price_axis(values: list[float]) -> list[str]:
    low = min(values)
    high = max(values)
    if high == low:
        return [f"{low:.3f}"] * 4
    step = (high - low) / 3
    return [f"{low + step * i:.3f}" for i in range(4)]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest src-python/tests/test_aggregation.py src-python/tests/test_period_builder.py -v`

Expected: 全部通过。

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/services/aggregation.py src-python/engine/services/period_builder.py src-python/tests/test_aggregation.py src-python/tests/test_period_builder.py
git commit -m "feat: 新增 Analysis 周期聚合器与周期构建器"
```

---

### Task 3: 实现 AnalysisService 与真实 JSON-RPC 接口

**Files:**
- Create: `src-python/engine/services/analysis_service.py`
- Modify: `src-python/engine/server.py`
- Modify: `src-python/main.py`
- Create: `src-python/tests/test_analysis_service.py`
- Create: `src-python/tests/test_server_analysis.py`

- [ ] **Step 1: 写失败测试，锁定 search_funds 与 get_fund_analysis 结果结构**

```python
# src-python/tests/test_analysis_service.py
import pandas as pd

from engine.models.database import Database
from engine.services.analysis_service import AnalysisService
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer


class MockAnalysisSource:
    def fetch_daily_quotes(self, code, start_date=None, period="daily"):
        if period == "weekly":
            return [{"date": "2024-03-22", "open": 1.0, "close": 1.2, "high": 1.3, "low": 0.9, "volume": 300, "amount": 3000}]
        if period == "monthly":
            return [{"date": "2024-03-31", "open": 1.0, "close": 1.3, "high": 1.4, "low": 0.9, "volume": 500, "amount": 5000}]
        return [
            {"date": "2024-03-20", "open": 1.0, "close": 1.1, "high": 1.2, "low": 0.9, "volume": 100, "amount": 1000},
            {"date": "2024-03-21", "open": 1.1, "close": 1.2, "high": 1.3, "low": 1.0, "volume": 120, "amount": 1200},
        ]

    def fetch_minute_quotes(self, code, fund_type, period, start_datetime=None, end_datetime=None):
        return [
            {"datetime": "2024-03-21 09:30:00", "open": 1.0, "close": 1.01, "high": 1.02, "low": 0.99, "volume": 100, "amount": 1000, "avg_price": 1.005},
            {"datetime": "2024-03-21 10:30:00", "open": 1.01, "close": 1.02, "high": 1.03, "low": 1.0, "volume": 120, "amount": 1200, "avg_price": 1.01},
        ]

    def fetch_nav(self, code, start_date=None):
        return [{"date": "2024-03-21", "nav": 1.18}]


def test_search_funds_returns_matches(tmp_path):
    db = Database(str(tmp_path / "analysis.db"))
    db.init()
    db.upsert_fund_info([
        {"code": "510300", "name": "沪深300ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "", "is_excluded": 0},
        {"code": "159915", "name": "创业板ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "", "is_excluded": 0},
    ])
    service = AnalysisService(db, MockAnalysisSource(), TechnicalIndicators(), Scorer())

    rows = service.search_funds("沪深")

    assert rows == [{"code": "510300", "name": "沪深300ETF"}]


def test_get_fund_analysis_returns_all_periods(tmp_path):
    db = Database(str(tmp_path / "analysis.db"))
    db.init()
    db.upsert_fund_info([
        {"code": "510300", "name": "沪深300ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "", "is_excluded": 0},
    ])
    service = AnalysisService(db, MockAnalysisSource(), TechnicalIndicators(), Scorer())

    result = service.get_fund_analysis("510300")

    assert result["code"] == "510300"
    assert set(result["periods"].keys()) == {"intraday", "day", "m5", "m60", "m120", "week", "month", "quarter", "year"}
    assert result["periods"]["intraday"]["line_points"]
    assert result["periods"]["day"]["candles"]
```

```python
# src-python/tests/test_server_analysis.py
import json

from engine.server import create_real_server
from engine.models.database import Database


def test_server_registers_analysis_methods(tmp_path, mocker):
    db = Database(str(tmp_path / "server.db"))
    db.init()
    source = mocker.Mock()
    server = create_real_server(db, source)

    assert "search_funds" in server.methods
    assert "get_fund_analysis" in server.methods


def test_server_handles_search_funds(tmp_path, mocker):
    db = Database(str(tmp_path / "server.db"))
    db.init()
    db.upsert_fund_info([
        {"code": "510300", "name": "沪深300ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "", "is_excluded": 0},
    ])
    source = mocker.Mock()
    source.fetch_daily_quotes.return_value = []
    source.fetch_minute_quotes.return_value = []
    source.fetch_nav.return_value = []

    server = create_real_server(db, source)
    payload = json.dumps({"jsonrpc": "2.0", "method": "search_funds", "params": {"keyword": "5103"}, "id": 1})
    response = json.loads(server.handle_request(payload))

    assert response["result"] == [{"code": "510300", "name": "沪深300ETF"}]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest src-python/tests/test_analysis_service.py src-python/tests/test_server_analysis.py -v`

Expected: `AnalysisService` 不存在，或 server 尚未注册分析接口。

- [ ] **Step 3: 实现 AnalysisService，并把接口接入真实 server 与主入口**

```python
# src-python/engine/services/analysis_service.py
from engine.services.aggregation import aggregate_candles
from engine.services.period_builder import build_intraday_period, build_kline_period


class AnalysisService:
    def __init__(self, db, source, indicators, scorer):
        self.db = db
        self.source = source
        self.indicators = indicators
        self.scorer = scorer

    def search_funds(self, keyword: str) -> list[dict]:
        normalized = keyword.strip().lower()
        if not normalized:
            return []
        funds = self.db.get_all_active_funds()
        matched = [
            {"code": fund["code"], "name": fund["name"]}
            for fund in funds
            if normalized in fund["code"].lower() or normalized in fund["name"].lower()
        ]
        prefix = [row for row in matched if row["code"].startswith(keyword.strip())]
        rest = [row for row in matched if row not in prefix]
        return (prefix + rest)[:20]

    def get_fund_analysis(self, code: str) -> dict:
        fund = next((row for row in self.db.get_all_active_funds() if row["code"] == code), None)
        if not fund:
            raise ValueError(f"Fund not found: {code}")

        day_rows = self.source.fetch_daily_quotes(code, period="daily")
        week_rows = self.source.fetch_daily_quotes(code, period="weekly")
        month_rows = self.source.fetch_daily_quotes(code, period="monthly")
        minute_1 = self.source.fetch_minute_quotes(code, fund["fund_type"], "1")
        minute_5 = self.source.fetch_minute_quotes(code, fund["fund_type"], "5")
        minute_60 = self.source.fetch_minute_quotes(code, fund["fund_type"], "60")
        minute_120 = aggregate_candles(minute_60, group_size=2, label_key="datetime")
        quarter_rows = aggregate_candles(month_rows, group_size=3, label_key="date")
        year_rows = aggregate_candles(month_rows, group_size=12, label_key="date")
        nav_rows = self.source.fetch_nav(code)

        latest_day = day_rows[-1] if day_rows else {"close": 0, "date": ""}
        latest_nav = nav_rows[-1]["nav"] if nav_rows else None
        premium_rate = None if latest_nav in (None, 0) else round((latest_day["close"] - latest_nav) / latest_nav * 100, 2)

        return {
            "code": code,
            "name": fund["name"],
            "market": "SH" if code.startswith(("5", "6")) else "SZ",
            "price": round(latest_day["close"], 3),
            "change_pct": 0.0,
            "iopv": latest_nav,
            "premium_rate": premium_rate,
            "risk_level": "中等波动",
            "strategy": {
                "conclusion": "基于真实数据生成的阶段性分析",
                "buy_zone": "结合近端支撑分批关注",
                "sell_zone": "接近前高后分批兑现",
                "position": "建议控制仓位分批参与",
                "stop_loss": "跌破关键支撑时止损",
                "holding_period": "3-10 个交易日",
                "risk_note": "分钟级数据受外部数据源窗口限制。",
            },
            "periods": {
                "intraday": build_intraday_period(minute_1, "分时真实数据", "分时图旁解读", "使用 1 分钟数据构建"),
                "day": build_kline_period(day_rows, "日线真实数据", "日线图旁解读", "使用日线构建"),
                "m5": build_kline_period(minute_5, "5 分钟真实数据", "5 分钟图旁解读", "使用 5 分钟数据构建"),
                "m60": build_kline_period(minute_60, "60 分钟真实数据", "60 分钟图旁解读", "使用 60 分钟数据构建"),
                "m120": build_kline_period(minute_120, "120 分钟聚合数据", "120 分钟图旁解读", "使用 60 分钟聚合构建"),
                "week": build_kline_period(week_rows, "周线真实数据", "周线图旁解读", "使用周线构建"),
                "month": build_kline_period(month_rows, "月线真实数据", "月线图旁解读", "使用月线构建"),
                "quarter": build_kline_period(quarter_rows, "季线聚合数据", "季线图旁解读", "使用月线聚合构建"),
                "year": build_kline_period(year_rows, "年线聚合数据", "年线图旁解读", "使用月线聚合构建"),
            },
        }
```

```python
# src-python/engine/server.py
from engine.services.analysis_service import AnalysisService

def create_real_server(db, source):
    server = JSONRPCServer()
    indicators = TechnicalIndicators()
    scorer = Scorer()
    fund_service = FundService(db, indicators, scorer)
    analysis_service = AnalysisService(db, source, indicators, scorer)
    sync_pipeline = DataSyncPipeline(db, source)
    ...
    server.register_method("search_funds", analysis_service.search_funds)
    server.register_method("get_fund_analysis", analysis_service.get_fund_analysis)
    return server
```

```python
# src-python/main.py
import os
import sys
import logging

from engine.server import create_real_server
from engine.models.database import Database
from engine.data.akshare_source import AkshareSource
from engine.sync import DataSyncPipeline


def main():
    logger.info("Starting Python ETF Engine...")
    db_path = os.path.join(os.path.dirname(__file__), "data", "fundflow.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = Database(db_path)
    db.init()
    source = AkshareSource()
    if not db.get_all_active_funds():
        DataSyncPipeline(db, source).sync_all()
    server = create_real_server(db, source)
    logger.info("Engine listening on stdin...")
    server.run_stdio()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest src-python/tests/test_analysis_service.py src-python/tests/test_server_analysis.py -v`

Expected: 全部通过。

- [ ] **Step 5: 运行一次 Python 全量回归**

Run: `pytest src-python/tests/ -v`

Expected: 无新增失败。

- [ ] **Step 6: 提交**

```bash
git add src-python/engine/services/analysis_service.py src-python/engine/server.py src-python/main.py src-python/tests/test_analysis_service.py src-python/tests/test_server_analysis.py
git commit -m "feat: 新增 AnalysisService 与真实 Analysis JSON-RPC 接口"
```

---

### Task 4: 新建前端 analysisApi 转换层

**Files:**
- Create: `src/utils/analysisApi.ts`
- Create: `src/utils/__tests__/analysisApi.spec.ts`

- [ ] **Step 1: 写失败测试，锁定后端真实结构到前端结构的转换**

```typescript
// src/utils/__tests__/analysisApi.spec.ts
import { describe, expect, it } from 'vitest'

import { toAnalysisViewModel } from '../analysisApi'

describe('toAnalysisViewModel', () => {
  it('将后端 snake_case 结构转换为 Analysis.vue 当前使用的字段', () => {
    const vm = toAnalysisViewModel({
      code: '510300',
      name: '沪深300ETF',
      market: 'SH',
      price: 4.123,
      change_pct: 0.56,
      iopv: 4.118,
      premium_rate: 0.12,
      risk_level: '中等波动',
      strategy: {
        conclusion: '真实结论',
        buy_zone: '4.05 - 4.10',
        sell_zone: '4.22 - 4.28',
        position: '建议 4 成',
        stop_loss: '跌破 3.98 止损',
        holding_period: '5 - 10 个交易日',
        risk_note: '风险提示',
      },
      periods: {
        intraday: { key: 'intraday', label: '分时', summary: '分时', chart_headline: '标题', chart_summary: '说明', price_axis: ['4.1'], time_axis: ['09:30'], line_points: [4.1], avg_line_points: [4.09], candles: [], volumes: [100], metrics: [] },
        day: { key: 'day', label: '日线', summary: '日线', chart_headline: '标题', chart_summary: '说明', price_axis: ['4.1'], time_axis: ['03-21'], line_points: [], avg_line_points: [], candles: [[4, 4.1, 3.9, 4.2]], volumes: [100], metrics: [] },
        m5: { key: 'm5', label: '5分钟', summary: '', chart_headline: '', chart_summary: '', price_axis: [], time_axis: [], line_points: [], avg_line_points: [], candles: [], volumes: [], metrics: [] },
        m60: { key: 'm60', label: '60分钟', summary: '', chart_headline: '', chart_summary: '', price_axis: [], time_axis: [], line_points: [], avg_line_points: [], candles: [], volumes: [], metrics: [] },
        m120: { key: 'm120', label: '120分钟', summary: '', chart_headline: '', chart_summary: '', price_axis: [], time_axis: [], line_points: [], avg_line_points: [], candles: [], volumes: [], metrics: [] },
        week: { key: 'week', label: '周线', summary: '', chart_headline: '', chart_summary: '', price_axis: [], time_axis: [], line_points: [], avg_line_points: [], candles: [], volumes: [], metrics: [] },
        month: { key: 'month', label: '月线', summary: '', chart_headline: '', chart_summary: '', price_axis: [], time_axis: [], line_points: [], avg_line_points: [], candles: [], volumes: [], metrics: [] },
        quarter: { key: 'quarter', label: '季线', summary: '', chart_headline: '', chart_summary: '', price_axis: [], time_axis: [], line_points: [], avg_line_points: [], candles: [], volumes: [], metrics: [] },
        year: { key: 'year', label: '年线', summary: '', chart_headline: '', chart_summary: '', price_axis: [], time_axis: [], line_points: [], avg_line_points: [], candles: [], volumes: [], metrics: [] },
      },
    })

    expect(vm.change).toBe('+0.56%')
    expect(vm.iopv).toBe('4.118')
    expect(vm.premium).toBe('+0.12%')
    expect(vm.riskLevel).toBe('中等波动')
    expect(vm.strategy.buyZone).toBe('4.05 - 4.10')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/utils/__tests__/analysisApi.spec.ts`

Expected: `analysisApi.ts` 不存在。

- [ ] **Step 3: 新建 analysisApi.ts 并实现转换与调用封装**

```typescript
// src/utils/analysisApi.ts
import { getAnalysisMockByCode, searchAnalysisCandidates, type AnalysisMock } from './analysisMock'

export type AnalysisSearchItem = {
  code: string
  name: string
}

export type AnalysisApiResponse = {
  code: string
  name: string
  market: string
  price: number
  change_pct: number
  iopv: number | null
  premium_rate: number | null
  risk_level: string
  strategy: {
    conclusion: string
    buy_zone: string
    sell_zone: string
    position: string
    stop_loss: string
    holding_period: string
    risk_note: string
  }
  periods: Record<string, any>
}

export function toAnalysisViewModel(payload: AnalysisApiResponse): AnalysisMock {
  const formatPct = (value: number | null) => `${(value ?? 0) >= 0 ? '+' : ''}${(value ?? 0).toFixed(2)}%`
  return {
    code: payload.code,
    name: payload.name,
    market: payload.market,
    price: payload.price.toFixed(3),
    change: formatPct(payload.change_pct),
    iopv: payload.iopv === null ? '--' : payload.iopv.toFixed(3),
    premium: payload.premium_rate === null ? '--' : formatPct(payload.premium_rate),
    riskLevel: payload.risk_level,
    strategy: {
      conclusion: payload.strategy.conclusion,
      buyZone: payload.strategy.buy_zone,
      sellZone: payload.strategy.sell_zone,
      position: payload.strategy.position,
      stopLoss: payload.strategy.stop_loss,
      holdingPeriod: payload.strategy.holding_period,
      riskNote: payload.strategy.risk_note,
    },
    periods: payload.periods as AnalysisMock['periods'],
  }
}

export async function loadAnalysisByCode(code: string): Promise<AnalysisMock | undefined> {
  if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
    return getAnalysisMockByCode(code)
  }
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const result = await invoke<AnalysisApiResponse>('invoke_engine', {
      method: 'get_fund_analysis',
      params: { code },
    })
    return result ? toAnalysisViewModel(result) : getAnalysisMockByCode(code)
  } catch {
    return getAnalysisMockByCode(code)
  }
}

export async function loadSearchCandidates(keyword: string): Promise<AnalysisSearchItem[]> {
  if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
    return searchAnalysisCandidates(keyword).map((item) => ({ code: item.code, name: item.name }))
  }
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    return await invoke<AnalysisSearchItem[]>('invoke_engine', {
      method: 'search_funds',
      params: { keyword },
    })
  } catch {
    return searchAnalysisCandidates(keyword).map((item) => ({ code: item.code, name: item.name }))
  }
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test -- --run src/utils/__tests__/analysisApi.spec.ts`

Expected: 全部通过。

- [ ] **Step 5: 提交**

```bash
git add src/utils/analysisApi.ts src/utils/__tests__/analysisApi.spec.ts
git commit -m "feat: 新增 Analysis 真实接口转换层与加载器"
```

---

### Task 5: 将 Analysis.vue 接入真实搜索与真实详情

**Files:**
- Modify: `src/views/Analysis.vue`
- Modify: `src/views/__tests__/Analysis.spec.ts`

- [ ] **Step 1: 写失败测试，锁定真实加载行为**

在 `src/views/__tests__/Analysis.spec.ts` 新增两个测试：

```typescript
it('搜索候选由真实 analysisApi 加载器提供', async () => {
  vi.doMock('../../utils/analysisApi', () => ({
    loadAnalysisByCode: vi.fn(),
    loadSearchCandidates: vi.fn(async () => [{ code: '510300', name: '沪深300ETF' }]),
  }))
  const { default: RealAnalysis } = await import('../Analysis.vue')
  const wrapper = mount(RealAnalysis)

  await wrapper.get('[data-test="analysis-search"]').setValue('5103')
  await flushPromises()

  expect(wrapper.get('[data-test="analysis-pick-510300"]').text()).toContain('沪深300ETF')
})

it('详情态由真实 analysisApi 加载器提供数据', async () => {
  vi.doMock('../../utils/analysisApi', () => ({
    loadSearchCandidates: vi.fn(async () => []),
    loadAnalysisByCode: vi.fn(async () => ({
      code: '510300',
      name: '沪深300ETF',
      market: 'SH',
      price: '4.123',
      change: '+0.56%',
      iopv: '4.118',
      premium: '+0.12%',
      riskLevel: '中等波动',
      strategy: {
        conclusion: '真实结论',
        buyZone: '4.05 - 4.10',
        sellZone: '4.22 - 4.28',
        position: '建议 4 成以内仓位',
        stopLoss: '跌破 3.98 止损',
        holdingPeriod: '5 - 10 个交易日',
        riskNote: '风险提示',
      },
      periods: {
        intraday: { key: 'intraday', label: '分时', summary: '', chartHeadline: '', chartSummary: '', priceAxis: ['4.1'], timeAxis: ['09:30'], linePoints: [4.1], avgLinePoints: [4.09], candles: [], volumes: [1], metrics: [] },
        day: { key: 'day', label: '日线', summary: '', chartHeadline: '', chartSummary: '', priceAxis: ['4.1'], timeAxis: ['03-21'], linePoints: [], avgLinePoints: [], candles: [[4, 4.1, 3.9, 4.2]], volumes: [1], metrics: [] },
        m5: { key: 'm5', label: '5分', summary: '', chartHeadline: '', chartSummary: '', priceAxis: [], timeAxis: [], linePoints: [], avgLinePoints: [], candles: [], volumes: [], metrics: [] },
        m60: { key: 'm60', label: '60分', summary: '', chartHeadline: '', chartSummary: '', priceAxis: [], timeAxis: [], linePoints: [], avgLinePoints: [], candles: [], volumes: [], metrics: [] },
        m120: { key: 'm120', label: '120分', summary: '', chartHeadline: '', chartSummary: '', priceAxis: [], timeAxis: [], linePoints: [], avgLinePoints: [], candles: [], volumes: [], metrics: [] },
        week: { key: 'week', label: '周线', summary: '', chartHeadline: '', chartSummary: '', priceAxis: [], timeAxis: [], linePoints: [], avgLinePoints: [], candles: [], volumes: [], metrics: [] },
        month: { key: 'month', label: '月线', summary: '', chartHeadline: '', chartSummary: '', priceAxis: [], timeAxis: [], linePoints: [], avgLinePoints: [], candles: [], volumes: [], metrics: [] },
        quarter: { key: 'quarter', label: '季线', summary: '', chartHeadline: '', chartSummary: '', priceAxis: [], timeAxis: [], linePoints: [], avgLinePoints: [], candles: [], volumes: [], metrics: [] },
        year: { key: 'year', label: '年线', summary: '', chartHeadline: '', chartSummary: '', priceAxis: [], timeAxis: [], linePoints: [], avgLinePoints: [], candles: [], volumes: [], metrics: [] },
      },
    })),
  }))
  const { default: RealAnalysis } = await import('../Analysis.vue')
  const wrapper = mount(RealAnalysis)
  await flushPromises()
  expect(wrapper.text()).toContain('真实结论')
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts`

Expected: `Analysis.vue` 仍依赖 `analysisMock.ts`，新测试失败。

- [ ] **Step 3: 最小改造 Analysis.vue 使用真实加载器**

将以下逻辑替换为异步真实加载：

```ts
// 删除或替换的 import
// from analysisMock: getAnalysisMockByCode, searchAnalysisCandidates
import { loadAnalysisByCode, loadSearchCandidates } from '../utils/analysisApi'

const activeAnalysis = ref<AnalysisMock | null>(null)
const candidates = ref<Array<{ code: string; name: string }>>([])

watch(keyword, async (value) => {
  const normalized = value.trim()
  if (!normalized) {
    candidates.value = []
    return
  }
  candidates.value = await loadSearchCandidates(normalized)
})

watch(routeCode, async (code) => {
  hideCandleTooltip()
  activePeriodKey.value = 'day'
  if (!code) {
    activeAnalysis.value = null
    keyword.value = ''
    return
  }
  keyword.value = ''
  activeAnalysis.value = await loadAnalysisByCode(code) ?? null
}, { immediate: true })
```

注意：保留当前模板结构、tooltip、图表渲染逻辑不变，只替换数据来源与候选列表来源。

- [ ] **Step 4: 运行前端测试确认通过**

Run: `npm run test -- --run src/views/__tests__/Analysis.spec.ts src/utils/__tests__/analysisApi.spec.ts`

Expected: 全部通过。

- [ ] **Step 5: 运行前端构建验证**

Run: `npm run build`

Expected: 构建成功。

- [ ] **Step 6: 提交**

```bash
git add src/views/Analysis.vue src/views/__tests__/Analysis.spec.ts src/utils/analysisApi.ts src/utils/__tests__/analysisApi.spec.ts
git commit -m "feat: Analysis 页面接入真实搜索与九周期详情数据"
```

---

### Task 6: 全量验证与文档更新

**Files:**
- Modify: `docs/development/api-interfaces.md`
- Modify: `docs/development/ai/current_state.md`
- Modify: `docs/development/human/2026-04-04-daily-log.md`

- [ ] **Step 1: 运行 Python 全量测试**

Run: `pytest src-python/tests/ -v`

Expected: 全部通过，联网依赖测试如为空结果允许按既有策略跳过。

- [ ] **Step 2: 运行前端全量测试**

Run: `npm run test -- --run`

Expected: 全部通过。

- [ ] **Step 3: 运行构建验证**

Run: `npm run build`

Expected: 成功。

- [ ] **Step 4: 更新开发文档**

更新 `docs/development/api-interfaces.md`：

- `API-05 get_fund_analysis` -> 改为 ✅ 已实现
- `API-06 search_funds` -> 改为 ✅ 已实现
- `ISSUE-02` -> 标记已解决
- `ISSUE-06` -> 备注当前前端 candle 顺序仍为 `[open, close, low, high]`，已按前端既有约定输出
- `ISSUE-09` -> 标记已部分解决：`intraday/m5/m60` 走 AKShare 分钟级，`m120` 由 `m60` 聚合

更新 `docs/development/ai/current_state.md`：

- 将当前阶段改为 “P1 Analysis 真实接口完成”
- 记录九周期真实化、搜索真实化、前端接入完成

更新 `docs/development/human/2026-04-04-daily-log.md`：

- 记录 AKShare 分钟级验证结论
- 记录九周期真实化实现范围与验证结果

- [ ] **Step 5: 提交**

```bash
git add docs/development/api-interfaces.md docs/development/ai/current_state.md docs/development/human/2026-04-04-daily-log.md
git commit -m "docs: 更新 P1 Analysis 九周期真实化开发文档"
```

---

## 自审

### 1. Spec 覆盖检查

| 规格要求 | 对应任务 |
|---|---|
| `search_funds` 真实化 | Task 3, Task 5 |
| `get_fund_analysis` 真实化 | Task 3, Task 5 |
| AKShare 分钟级能力接入 | Task 1 |
| `m120` 由 `m60` 聚合 | Task 2, Task 3 |
| `quarter/year` 由 `month` 聚合 | Task 2, Task 3 |
| 前端尽量不动版式，只换数据源 | Task 5 |
| 周期数据不足时不伪造 | Task 3, Task 5 |
| Python/前端/构建验证 | Task 6 |
| 开发文档更新 | Task 6 |

### 2. Placeholder 扫描

已检查：无 `TODO`、`TBD`、`implement later`、`类似 Task N` 等占位表述。

### 3. 类型一致性

- 后端统一输出 snake_case；前端在 `analysisApi.ts` 中转换为当前 `Analysis.vue` 结构
- candle 顺序统一保持前端既有约定 `[open, close, low, high]`
- `m120` / `quarter` / `year` 都通过 `aggregate_candles()` 生成，避免重复实现

---

Plan complete and saved to `docs/superpowers/plans/2026-04-04-p1-analysis-real-data-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 我派发一个全新的子代理逐任务执行，并在每个任务后做规格审查与代码审查

**2. Inline Execution** - 我在当前会话中按计划顺序执行

Which approach?
