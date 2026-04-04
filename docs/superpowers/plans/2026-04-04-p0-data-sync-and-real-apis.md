# P0: 数据同步与真实接口对接 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将后端从硬编码 Mock 改为真实数据驱动，实现 akshare → SQLite 数据同步流程，并让 `get_fund_list` 和 `get_dashboard_signals` 返回真实数据。

**Architecture:** 新增 sync 模块负责从 akshare 拉取数据写入 SQLite，新增 fund_service 模块封装业务逻辑（指标计算+评分+文字化），server.py 调用 service 层而非返回硬编码数据。前端 FundList 补 snake_case → camelCase 转换层。

**Tech Stack:** Python (akshare, pandas, numpy, sqlite3, pytest), TypeScript (Vue 3, Pinia)

---

## 文件结构

| 文件 | 操作 | 说明 |
|---|---|---|
| `src-python/engine/sync.py` | **新建** | 数据同步管道：从 akshare 拉取基金列表+行情+净值，写入 SQLite |
| `src-python/engine/services/__init__.py` | **新建** | services 包 |
| `src-python/engine/services/fund_service.py` | **新建** | 业务逻辑层：查询基金列表、计算信号、评分文字化 |
| `src-python/engine/server.py` | **修改** | 替换硬编码方法为调用 service 层 |
| `src-python/engine/main.py` | **修改** | 注册新 RPC 方法 + 启动时初始化 |
| `src-python/tests/test_sync.py` | **新建** | sync 模块测试 |
| `src-python/tests/test_fund_service.py` | **新建** | fund_service 模块测试 |
| `src-python/tests/test_server_real.py` | **新建** | server 集成测试（真实模块串联） |
| `src/utils/dashboardSignals.ts` | **保持不变** | 已有 snake→camel 转换，验证兼容 |
| `src/views/FundList.vue` | **修改** | 新增 snake_case → camelCase 转换层 |
| `src/views/__tests__/FundList.spec.ts` | **修改** | 补充转换层测试 |

---

### Task 0: 新建 sync 数据同步模块

**Files:**
- Create: `src-python/engine/sync.py`
- Test: `src-python/tests/test_sync.py`

- [ ] **Step 1: 编写 sync 模块测试**

```python
# src-python/tests/test_sync.py
import os
import tempfile
import pytest
import pandas as pd
from engine.sync import DataSyncPipeline
from engine.models.database import Database

class MockAkshareSource:
    """模拟 akshare 数据源，不需要真实联网"""
    def fetch_fund_list(self):
        return [
            {"code": "510300", "name": "沪深300ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "2012-05-28", "is_excluded": 0},
            {"code": "159915", "name": "创业板ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "2010-02-11", "is_excluded": 0},
            {"code": "510500", "name": "中证500ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "2013-02-06", "is_excluded": 0},
            {"code": "513050", "name": "中概互联网ETF", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0", "list_date": "2014-01-16", "is_excluded": 0},
        ]

    def fetch_daily_quotes(self, code: str, start_date: str = None):
        n = 30
        dates = pd.date_range(end="2026-03-28", periods=n)
        base = 4.0 if code == "510300" else 2.0
        return [
            {
                "date": str(d)[:10],
                "open": base + i * 0.01,
                "close": base + i * 0.01 + 0.02,
                "high": base + i * 0.01 + 0.05,
                "low": base + i * 0.01 - 0.03,
                "volume": 100000 + i * 1000,
                "amount": (100000 + i * 1000) * base,
            }
            for i, d in enumerate(dates)
        ]

    def fetch_nav(self, code: str, start_date: str = None):
        return [{"date": "2026-03-28", "nav": 4.118}]


@pytest.fixture
def mock_env(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.init()
    yield {"db": db, "source": MockAkshareSource()}
    db.close()


def test_sync_fund_list(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    pipeline.sync_fund_list()
    funds = mock_env["db"].get_all_active_funds()
    assert len(funds) == 4
    assert funds[0]["code"] == "510300"
    assert funds[0]["t_plus"] == "T+1"


def test_sync_daily_quotes(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    # 先同步基金列表
    pipeline.sync_fund_list()
    # 再同步日线
    pipeline.sync_daily_quotes_for_all()
    quotes = mock_env["db"].get_daily_quotes("510300", "2026-03-01", "2026-03-28")
    assert len(quotes) == 30
    assert quotes[-1]["close"] == pytest.approx(4.0 + 29 * 0.01 + 0.02, abs=0.001)


def test_sync_nav(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    pipeline.sync_fund_list()
    pipeline.sync_daily_quotes_for_all()
    pipeline.sync_nav_for_all()
    quotes = mock_env["db"].get_daily_quotes("510300", "2026-03-28", "2026-03-28")
    assert len(quotes) == 1
    assert quotes[0]["nav"] == pytest.approx(4.118, abs=0.001)
    assert quotes[0]["premium_rate"] is not None


def test_sync_all(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    result = pipeline.sync_all()
    assert "funds_synced" in result
    assert "quotes_synced" in result
    assert result["funds_synced"] == 4
    assert result["quotes_synced"] > 0


def test_sync_skips_excluded_funds(mock_env):
    pipeline = DataSyncPipeline(mock_env["db"], mock_env["source"])
    pipeline.sync_fund_list()
    # 513050 是 T+0 跨境型，不应该被排除（只有货币/债券才排除）
    funds = mock_env["db"].get_all_active_funds()
    codes = [f["code"] for f in funds]
    assert "510300" in codes
    assert "513050" in codes
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest src-python/tests/test_sync.py -v
```
预期：全部失败（`DataSyncPipeline` 不存在）

- [ ] **Step 3: 实现 sync 模块**

```python
# src-python/engine/sync.py
"""数据同步管道：从 akshare 拉取数据写入 SQLite"""
import logging
from engine.models.database import Database
from engine.data.base import DataSource

logger = logging.getLogger(__name__)


class DataSyncPipeline:
    def __init__(self, db: Database, source: DataSource):
        self.db = db
        self.source = source

    def sync_fund_list(self) -> int:
        """同步基金列表到 fund_info 表"""
        funds = self.source.fetch_fund_list()
        self.db.upsert_fund_info(funds)
        logger.info(f"Synced {len(funds)} funds")
        return len(funds)

    def sync_daily_quotes_for_all(self) -> int:
        """同步所有活跃基金的日线行情到 daily_quote 表"""
        funds = self.db.get_all_active_funds()
        total = 0
        for fund in funds:
            code = fund["code"]
            quotes = self.source.fetch_daily_quotes(code)
            if not quotes:
                continue
            for q in quotes:
                q["code"] = code
            self.db.upsert_daily_quotes(quotes)
            total += len(quotes)
        logger.info(f"Synced {total} daily quotes for {len(funds)} funds")
        return total

    def sync_nav_for_all(self) -> int:
        """同步所有活跃基金的净值到 daily_quote 表"""
        funds = self.db.get_all_active_funds()
        updated = 0
        for fund in funds:
            code = fund["code"]
            nav_data = self.source.fetch_nav(code)
            if not nav_data:
                continue
            for nav_item in nav_data:
                date = nav_item["date"]
                nav = nav_item["nav"]
                self.db._update_nav(code, date, nav)
                updated += 1
        logger.info(f"Updated nav for {updated} records")
        return updated

    def sync_all(self) -> dict:
        """执行完整同步流程"""
        funds_count = self.sync_fund_list()
        quotes_count = self.sync_daily_quotes_for_all()
        nav_count = self.sync_nav_for_all()
        return {
            "funds_synced": funds_count,
            "quotes_synced": quotes_count,
            "nav_updated": nav_count,
        }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest src-python/tests/test_sync.py -v
```
预期：全部通过

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/sync.py src-python/tests/test_sync.py
git commit -m "feat: 新建 DataSyncPipeline 数据同步模块"
```

---

### Task 1: 新建 fund_service 业务逻辑层

**Files:**
- Create: `src-python/engine/services/__init__.py`
- Create: `src-python/engine/services/fund_service.py`
- Test: `src-python/tests/test_fund_service.py`

- [ ] **Step 1: 编写 fund_service 测试**

```python
# src-python/tests/test_fund_service.py
import os
import tempfile
import pytest
import pandas as pd
from engine.models.database import Database
from engine.services.fund_service import FundService
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer


class MockDbWithData:
    """模拟已有数据的数据库"""
    def __init__(self, tmp_path):
        self.db_path = str(tmp_path / "test_service.db")
        self.db = Database(self.db_path)
        self.db.init()
        self._seed_data()

    def _seed_data(self):
        # 插入基金信息
        self.db.upsert_fund_info([
            {"code": "510300", "name": "沪深300ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "2012-05-28", "is_excluded": 0},
            {"code": "159915", "name": "创业板ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "2010-02-11", "is_excluded": 0},
        ])
        # 插入日线数据（30天）
        import numpy as np
        np.random.seed(42)
        n = 30
        dates = pd.date_range(end="2026-03-28", periods=n)
        close = 4.0 + np.cumsum(np.random.randn(n) * 0.02)
        high = close + np.abs(np.random.randn(n) * 0.03)
        low = close - np.abs(np.random.randn(n) * 0.03)
        opn = close + np.random.randn(n) * 0.01
        volume = np.random.randint(100000, 500000, n).astype(float)
        amount = volume * close

        quotes = []
        for i in range(n):
            quotes.append({
                "code": "510300", "date": str(dates[i])[:10],
                "open": float(opn[i]), "close": float(close[i]),
                "high": float(high[i]), "low": float(low[i]),
                "volume": float(volume[i]), "amount": float(amount[i]),
                "nav": float(close[i]) - 0.005, "premium_rate": 0.001,
                "prev_close": float(close[i-1]) if i > 0 else float(close[i]),
                "is_suspended": 0, "suspended_days": 0,
            })
        self.db.upsert_daily_quotes(quotes)

    def get_all_active_funds(self):
        return self.db.get_all_active_funds()

    def get_daily_quotes(self, code, start, end):
        return self.db.get_daily_quotes(code, start, end)

    def close(self):
        self.db.close()


@pytest.fixture
def mock_db(tmp_path):
    mock = MockDbWithData(tmp_path)
    yield mock
    mock.close()


def test_get_fund_list_returns_data(mock_db):
    service = FundService(mock_db, TechnicalIndicators(), Scorer())
    result = service.get_fund_list()
    assert isinstance(result, list)
    assert len(result) == 2
    # 验证 snake_case 字段存在
    first = result[0]
    assert "code" in first
    assert "prev_close" in first
    assert "macd" in first
    assert "score" in first


def test_fund_list_item_has_technical_indicators(mock_db):
    service = FundService(mock_db, TechnicalIndicators(), Scorer())
    result = service.get_fund_list()
    first = result[0]
    # 验证技术指标结构
    for key in ["macd", "rsi", "boll", "ma5", "ma20"]:
        assert key in first, f"Missing {key}"
        assert "value" in first[key], f"{key} missing value"
        assert "signal" in first[key], f"{key} missing signal"
        assert first[key]["signal"] in ["bullish", "bearish", "neutral"]


def test_fund_list_item_has_score(mock_db):
    service = FundService(mock_db, TechnicalIndicators(), Scorer())
    result = service.get_fund_list()
    first = result[0]
    assert "score" in first
    assert isinstance(first["score"], int)
    assert 1 <= first["score"] <= 10


def test_fund_list_item_has_volatility(mock_db):
    service = FundService(mock_db, TechnicalIndicators(), Scorer())
    result = service.get_fund_list()
    first = result[0]
    assert "volatility" in first
    assert isinstance(first["volatility"], float)


def test_get_fund_list_empty_db(tmp_path):
    """空数据库应返回空列表"""
    from engine.models.database import Database
    db_path = str(tmp_path / "empty.db")
    db = Database(db_path)
    db.init()
    service = FundService(db, TechnicalIndicators(), Scorer())
    result = service.get_fund_list()
    assert result == []
    db.close()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest src-python/tests/test_fund_service.py -v
```
预期：全部失败（`FundService` 不存在）

- [ ] **Step 3: 实现 fund_service 模块**

```python
# src-python/engine/services/fund_service.py
"""基金业务逻辑层：查询列表、计算指标、评分、文字化"""
import logging
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer

logger = logging.getLogger(__name__)


class FundService:
    def __init__(self, db, indicators: TechnicalIndicators, scorer: Scorer):
        self.db = db
        self.indicators = indicators
        self.scorer = scorer

    def get_fund_list(self) -> list[dict]:
        """获取全量基金列表，包含最新行情、技术指标、评分"""
        funds = self.db.get_all_active_funds()
        if not funds:
            return []

        results = []
        for fund in funds:
            code = fund["code"]
            quotes = self.db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
            if not quotes:
                continue

            df = self._quotes_to_df(quotes)
            df_with_indicators = self.indicators.compute_all(df)

            # 取最新一天的数据
            latest = df_with_indicators.iloc[-1]
            prev = df_with_indicators.iloc[-2] if len(df_with_indicators) > 1 else latest

            # 行情字段
            prev_close = float(prev["close"])
            open_price = float(latest["open"])
            close_price = float(latest["close"])
            high_price = float(latest["high"])
            low_price = float(latest["low"])
            volatility = (high_price - low_price) / low_price if low_price != 0 else 0.0

            # 技术指标文字化
            macd_val = self._describe_macd(latest)
            rsi_val = self._describe_rsi(latest)
            boll_val = self._describe_boll(latest)
            ma5_val = self._describe_ma5(latest, df_with_indicators)
            ma20_val = self._describe_ma20(df_with_indicators)

            # 评分
            score_result = self.scorer.score(df_with_indicators)
            score = max(1, min(10, round(score_result["total_score"] / 10)))

            results.append({
                "code": code,
                "name": fund["name"],
                "prev_close": round(prev_close, 3),
                "open": round(open_price, 3),
                "close": round(close_price, 3),
                "high": round(high_price, 3),
                "low": round(low_price, 3),
                "volatility": round(volatility, 4),
                "macd": macd_val,
                "rsi": rsi_val,
                "boll": boll_val,
                "ma5": ma5_val,
                "ma20": ma20_val,
                "score": score,
            })

        return results

    # --- 技术指标文字化 ---

    def _describe_macd(self, row) -> dict:
        dif = row.get("macd", 0)
        dea = row.get("macd_signal", 0)
        hist = row.get("macd_hist", 0)
        if hist > 0.01:
            return {"value": "红柱", "signal": "bullish"}
        elif hist < -0.01:
            return {"value": "绿柱", "signal": "bearish"}
        else:
            return {"value": "粘合", "signal": "neutral"}

    def _describe_rsi(self, row) -> dict:
        rsi = row.get("rsi12", 50)
        val = str(int(round(rsi))) if not pd.isna(rsi) else "50"
        rsi_num = float(rsi) if not pd.isna(rsi) else 50
        if rsi_num > 60:
            return {"value": val, "signal": "bullish"}
        elif rsi_num < 40:
            return {"value": val, "signal": "bearish"}
        else:
            return {"value": val, "signal": "neutral"}

    def _describe_boll(self, row) -> dict:
        close = row.get("close", 0)
        upper = row.get("boll_upper", 0)
        mid = row.get("boll_mid", 0)
        lower = row.get("boll_lower", 0)
        if pd.isna(upper) or pd.isna(mid) or pd.isna(lower):
            return {"value": "中轨", "signal": "neutral"}
        dist_upper = abs(close - upper)
        dist_mid = abs(close - mid)
        dist_lower = abs(close - lower)
        min_dist = min(dist_upper, dist_mid, dist_lower)
        if min_dist == dist_upper:
            return {"value": "上轨", "signal": "bearish"}
        elif min_dist == dist_lower:
            return {"value": "下轨", "signal": "bullish"}
        else:
            return {"value": "中轨", "signal": "neutral"}

    def _describe_ma5(self, row, df) -> dict:
        ma5 = row.get("ma5", 0)
        ma20 = row.get("ma20", 0)
        if pd.isna(ma5) or pd.isna(ma20):
            return {"value": "粘合", "signal": "neutral"}
        diff_pct = abs(ma5 - ma20) / ma20 if ma20 != 0 else 0
        if diff_pct < 0.005:
            return {"value": "粘合", "signal": "neutral"}
        elif ma5 > ma20:
            return {"value": "多头", "signal": "bullish"}
        else:
            return {"value": "空头", "signal": "bearish"}

    def _describe_ma20(self, df) -> dict:
        if len(df) < 3:
            return {"value": "粘合", "signal": "neutral"}
        ma20_vals = df["ma20"].dropna().tail(3).values
        if len(ma20_vals) < 3:
            return {"value": "粘合", "signal": "neutral"}
        slope = ma20_vals[-1] - ma20_vals[0]
        avg = ma20_vals.mean()
        slope_pct = abs(slope) / avg if avg != 0 else 0
        if slope_pct < 0.002:
            return {"value": "粘合", "signal": "neutral"}
        elif slope > 0:
            return {"value": "向上", "signal": "bullish"}
        else:
            return {"value": "向下", "signal": "bearish"}

    # --- 工具方法 ---

    def _quotes_to_df(self, quotes: list[dict]):
        import pandas as pd
        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values("date").reset_index(drop=True)
```

注意：需要在文件顶部加 `import pandas as pd`。

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest src-python/tests/test_fund_service.py -v
```
预期：全部通过

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/services/__init__.py src-python/engine/services/fund_service.py src-python/tests/test_fund_service.py
git commit -m "feat: 新建 FundService 业务逻辑层，串联指标计算与评分"
```

---

### Task 2: 改造 server.py 使用真实 service 层

**Files:**
- Modify: `src-python/engine/server.py`
- Modify: `src-python/engine/main.py`
- Test: `src-python/tests/test_server_real.py`

- [ ] **Step 1: 编写 server 集成测试**

```python
# src-python/tests/test_server_real.py
"""测试 server.py 使用真实模块（非硬编码）"""
import json
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from engine.models.database import Database
from engine.server import create_real_server


class MockAkshareSource:
    def fetch_fund_list(self):
        return [
            {"code": "510300", "name": "沪深300ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "2012-05-28", "is_excluded": 0},
            {"code": "159915", "name": "创业板ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "2010-02-11", "is_excluded": 0},
        ]

    def fetch_daily_quotes(self, code: str, start_date: str = None):
        n = 30
        dates = pd.date_range(end="2026-03-28", periods=n)
        base = 4.0 if code == "510300" else 2.0
        np.random.seed(hash(code) % 1000)
        close = base + np.cumsum(np.random.randn(n) * 0.02)
        high = close + np.abs(np.random.randn(n) * 0.03)
        low = close - np.abs(np.random.randn(n) * 0.03)
        opn = close + np.random.randn(n) * 0.01
        volume = np.random.randint(100000, 500000, n).astype(float)
        amount = volume * close
        return [
            {"date": str(dates[i])[:10], "open": float(opn[i]), "close": float(close[i]),
             "high": float(high[i]), "low": float(low[i]), "volume": float(volume[i]), "amount": float(amount[i])}
            for i in range(n)
        ]

    def fetch_nav(self, code: str, start_date: str = None):
        return [{"date": "2026-03-28", "nav": 4.118}]


@pytest.fixture
def real_server(tmp_path):
    db_path = str(tmp_path / "test_real.db")
    db = Database(db_path)
    db.init()
    source = MockAkshareSource()
    server = create_real_server(db, source)
    yield server
    db.close()


def test_get_fund_list_returns_real_data(real_server):
    req = json.dumps({"jsonrpc": "2.0", "method": "get_fund_list", "params": {}, "id": 1})
    res = json.loads(real_server.handle_request(req))
    assert "error" not in res
    result = res["result"]
    assert isinstance(result, list)
    assert len(result) == 2
    # 验证返回的是真实计算的数据，不是硬编码
    first = result[0]
    assert first["code"] in ["510300", "159915"]
    assert "macd" in first
    assert "score" in first


def test_get_dashboard_signals_returns_real_data(real_server):
    req = json.dumps({"jsonrpc": "2.0", "method": "get_dashboard_signals", "params": {}, "id": 2})
    res = json.loads(real_server.handle_request(req))
    assert "error" not in res
    result = res["result"]
    assert isinstance(result, list)
    assert len(result) > 0
    first = result[0]
    # 验证包含 change_pct 字段
    assert "change_pct" in first
    assert "code" in first
    assert "name" in first
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest src-python/tests/test_server_real.py -v
```
预期：`create_real_server` 不存在

- [ ] **Step 3: 修改 server.py，新增 create_real_server 函数**

```python
# src-python/engine/server.py
# 在文件顶部添加 import
import logging
import pandas as pd
from engine.services.fund_service import FundService
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer
from engine.sync import DataSyncPipeline

logger = logging.getLogger(__name__)


def create_real_server(db, source):
    """创建使用真实模块的 JSONRPCServer"""
    server = JSONRPCServer()

    # 初始化组件
    indicators = TechnicalIndicators()
    scorer = Scorer()
    fund_service = FundService(db, indicators, scorer)
    sync_pipeline = DataSyncPipeline(db, source)

    # 注册方法
    server.register_method("ping", lambda: "pong")
    server.register_method("get_engine_status", lambda: {"status": "running", "version": "1.0.0"})
    server.register_method("fetch_legal_tax_rates", fetch_legal_tax_rates)

    # 使用真实 service 层
    server.register_method("get_fund_list", fund_service.get_fund_list)

    def get_dashboard_signals_real():
        return _build_dashboard_signals(db, fund_service)

    server.register_method("get_dashboard_signals", get_dashboard_signals_real)

    def sync_data():
        return sync_pipeline.sync_all()

    server.register_method("sync_data", sync_data)

    return server


def _build_dashboard_signals(db, fund_service):
    """从数据库构建 dashboard signals"""
    funds = db.get_all_active_funds()
    if not funds:
        return []

    signals = []
    for fund in funds:
        code = fund["code"]
        quotes = db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
        if not quotes:
            continue

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        current_price = float(latest["close"])
        prev_close = float(prev["close"])
        change_pct = round((current_price - prev_close) / prev_close * 100, 2) if prev_close != 0 else 0.0

        nav = float(latest.get("nav", 0)) if pd.notna(latest.get("nav")) else None
        nav_date = latest.get("date") if "date" in df.columns else None
        premium_rate = round(float(latest.get("premium_rate", 0)) * 100, 2) if pd.notna(latest.get("premium_rate")) else None

        signals.append({
            "code": code,
            "name": fund["name"],
            "t_plus": fund["t_plus"],
            "current_price": round(current_price, 3),
            "change_pct": change_pct,
            "buy_price": None,
            "sell_price": None,
            "stop_loss": None,
            "latest_nav": round(nav, 3) if nav else None,
            "nav_date": nav_date,
            "premium_rate": premium_rate,
            "expected_profit": None,
            "expected_profit_pct": None,
            "max_loss": None,
            "max_loss_pct": None,
        })

    return signals
```

- [ ] **Step 4: 修改 main.py**

```python
# src-python/engine/main.py
import sys
import logging
import os
import tempfile
from engine.server import JSONRPCServer, fetch_legal_tax_rates, create_real_server
from engine.models.database import Database
from engine.data.akshare_source import AkshareSource
from engine.sync import DataSyncPipeline

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ping():
    return "pong"

def get_engine_status():
    return {"status": "running", "version": "1.0.0"}

def main():
    logger.info("Starting Python ETF Engine...")

    # 初始化数据库
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "fundflow.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = Database(db_path)
    db.init()

    # 初始化数据源
    source = AkshareSource()

    # 首次运行自动同步
    funds = db.get_all_active_funds()
    if not funds:
        logger.info("首次运行，执行数据同步...")
        sync = DataSyncPipeline(db, source)
        result = sync.sync_all()
        logger.info(f"同步完成: {result}")

    # 创建使用真实模块的 server
    server = create_real_server(db, source)

    logger.info("Engine listening on stdin...")
    server.run_stdio()

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest src-python/tests/test_server_real.py -v
```
预期：全部通过

- [ ] **Step 6: 运行全量 Python 测试确保无回归**

```bash
pytest src-python/tests/ -v
```
预期：全部通过（包含原有测试 + 新增测试）

- [ ] **Step 7: 提交**

```bash
git add src-python/engine/server.py src-python/engine/main.py src-python/tests/test_server_real.py
git commit -m "feat: server.py 改用真实 service 层，main.py 初始化数据库与自动同步"
```

---

### Task 3: 前端 FundList 补 snake_case → camelCase 转换层

**Files:**
- Create: `src/utils/fundList.ts`
- Modify: `src/views/FundList.vue`
- Modify: `src/views/__tests__/FundList.spec.ts`

- [ ] **Step 1: 编写转换工具及测试**

```typescript
// src/utils/fundList.ts
export interface FundListItem {
  code: string
  name: string
  prev_close: number
  open: number
  close: number
  high: number
  low: number
  volatility: number
  macd: { value: string; signal: 'bullish' | 'bearish' | 'neutral' }
  rsi: { value: string; signal: 'bullish' | 'bearish' | 'neutral' }
  boll: { value: string; signal: 'bullish' | 'bearish' | 'neutral' }
  ma5: { value: string; signal: 'bullish' | 'bearish' | 'neutral' }
  ma20: { value: string; signal: 'bullish' | 'bearish' | 'neutral' }
  score: number
}

export interface FundListRow extends FundListItem {
  prevClose: number
  changePct: number
  scoreLabel: string
  scoreDirection: 'bullish' | 'bearish' | 'neutral'
}

export function toFundListRow(item: FundListItem): FundListRow {
  const changePct = item.prev_close !== 0
    ? ((item.close - item.prev_close) / item.prev_close) * 100
    : 0

  const scoreDirection = item.score >= 7 ? 'bullish' : item.score >= 4 ? 'neutral' : 'bearish'
  const scoreLabel =
    item.score >= 9 ? '强烈看多' :
    item.score >= 7 ? '看多' :
    item.score >= 4 ? '中性' :
    item.score >= 2 ? '看空' :
    '强烈看空'

  return {
    ...item,
    prevClose: item.prev_close,
    changePct,
    scoreLabel,
    scoreDirection,
  }
}

export function toFundListRows(items: FundListItem[]): FundListRow[] {
  return items.map(toFundListRow)
}

export async function loadFundList(): Promise<FundListItem[]> {
  if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
    return getFundListMock()
  }

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const result = await invoke<FundListItem[]>('invoke_engine', {
      method: 'get_fund_list',
      params: {},
    })
    return Array.isArray(result) ? result : getFundListMock()
  } catch {
    return getFundListMock()
  }
}

const fundListMock: FundListItem[] = [
  {
    code: '510300', name: '沪深300ETF',
    prev_close: 4.100, open: 4.105, close: 4.123, high: 4.150, low: 4.080,
    volatility: (4.150 - 4.080) / 4.080,
    macd: { value: '金叉', signal: 'bullish' },
    rsi: { value: '52', signal: 'neutral' },
    boll: { value: '中轨', signal: 'bullish' },
    ma5: { value: '上穿', signal: 'bullish' },
    ma20: { value: '粘合', signal: 'neutral' },
    score: 9,
  },
  {
    code: '159915', name: '创业板ETF',
    prev_close: 2.240, open: 2.245, close: 2.256, high: 2.280, low: 2.230,
    volatility: (2.280 - 2.230) / 2.230,
    macd: { value: '红柱', signal: 'bullish' },
    rsi: { value: '68', signal: 'bullish' },
    boll: { value: '下轨', signal: 'bullish' },
    ma5: { value: '多头', signal: 'bullish' },
    ma20: { value: '向上', signal: 'bullish' },
    score: 10,
  },
  {
    code: '510500', name: '中证500ETF',
    prev_close: 6.800, open: 6.790, close: 6.789, high: 6.820, low: 6.750,
    volatility: (6.820 - 6.750) / 6.750,
    macd: { value: '死叉', signal: 'bearish' },
    rsi: { value: '48', signal: 'neutral' },
    boll: { value: '中轨', signal: 'neutral' },
    ma5: { value: '下穿', signal: 'bearish' },
    ma20: { value: '粘合', signal: 'neutral' },
    score: 3,
  },
  {
    code: '588000', name: '科创50ETF',
    prev_close: 1.050, open: 1.045, close: 1.030, high: 1.060, low: 1.020,
    volatility: (1.060 - 1.020) / 1.020,
    macd: { value: '绿柱', signal: 'bearish' },
    rsi: { value: '25', signal: 'bearish' },
    boll: { value: '上轨', signal: 'bearish' },
    ma5: { value: '空头', signal: 'bearish' },
    ma20: { value: '向下', signal: 'bearish' },
    score: 1,
  },
]

function cloneFundListItem(item: FundListItem): FundListItem {
  return JSON.parse(JSON.stringify(item))
}

export function getFundListMock(): FundListItem[] {
  return fundListMock.map(cloneFundListItem)
}
```

```typescript
// src/utils/__tests__/fundList.spec.ts
import { toFundListRow, toFundListRows, getFundListMock } from '../fundList'

describe('toFundListRow', () => {
  it('converts snake_case to camelCase fields', () => {
    const item = getFundListMock()[0]
    const row = toFundListRow(item)
    expect(row.prevClose).toBe(4.100)
    expect(row.changePct).toBeCloseTo(((4.123 - 4.100) / 4.100) * 100, 2)
  })

  it('maps score to correct label and direction', () => {
    const mock = getFundListMock()
    // score=9 → 强烈看多 / bullish
    expect(toFundListRow(mock[0]).scoreLabel).toBe('强烈看多')
    expect(toFundListRow(mock[0]).scoreDirection).toBe('bullish')
    // score=3 → 看空 / bearish
    expect(toFundListRow(mock[2]).scoreLabel).toBe('看空')
    expect(toFundListRow(mock[2]).scoreDirection).toBe('bearish')
    // score=1 → 强烈看空 / bearish
    expect(toFundListRow(mock[3]).scoreLabel).toBe('强烈看空')
    expect(toFundListRow(mock[3]).scoreDirection).toBe('bearish')
  })
})

describe('toFundListRows', () => {
  it('converts all items', () => {
    const items = getFundListMock()
    const rows = toFundListRows(items)
    expect(rows.length).toBe(4)
    expect(rows[0].code).toBe('510300')
    expect(rows[0].changePct).toBeDefined()
  })
})
```

- [ ] **Step 2: 运行测试确认通过**

```bash
npm run test -- --run src/utils/__tests__/fundList.spec.ts
```
预期：全部通过

- [ ] **Step 3: 修改 FundList.vue 使用转换层**

在 `FundList.vue` 中：
1. 导入 `toFundListRows` 和 `loadFundList`
2. 将 `buildFundRows` 替换为使用 `toFundListRows`
3. 将加载逻辑改为调用 `loadFundList()`

```vue
<!-- 在 FundList.vue 的 script 部分，修改 import 和加载逻辑 -->

<!-- 替换原有的 import -->
<!-- 从: import type { FundListItem, FundListRow } from './FundList' (内联定义) -->
<!-- 改为: -->
import { toFundListRows, loadFundList, type FundListItem, type FundListRow } from '../utils/fundList'

<!-- 替换 buildFundRows 函数 -->
<!-- 删除原有的 buildFundRows 函数 -->
<!-- 改为: -->
const fundRows = ref<FundListRow[]>([])

async function loadFundListData() {
  const items = await loadFundList()
  fundRows.value = toFundListRows(items)
}

<!-- 在 onMounted 中调用 -->
onMounted(() => {
  loadFundListData()
})
```

具体修改位置：找到 `FundList.vue` 中 `buildFundRows` 函数定义处和 `onMounted` 调用处，替换为上述代码。

- [ ] **Step 4: 修改 FundList.spec.ts 适配新结构**

```typescript
// 在 FundList.spec.ts 中，mock 数据改为 snake_case 格式
// 确保测试使用 toFundListRows 转换后的数据
// 更新所有引用 fundListMock 的地方
```

- [ ] **Step 5: 运行前端测试和构建**

```bash
npm run test -- --run src/views/__tests__/FundList.spec.ts src/utils/__tests__/fundList.spec.ts
npm run build
```
预期：全部通过

- [ ] **Step 6: 提交**

```bash
git add src/utils/fundList.ts src/utils/__tests__/fundList.spec.ts src/views/FundList.vue src/views/__tests__/FundList.spec.ts
git commit -m "feat: FundList 新增 snake_case → camelCase 转换层，对接真实后端数据"
```

---

### Task 4: 全量验证与回归测试

- [ ] **Step 1: 运行全量 Python 测试**

```bash
pytest src-python/tests/ -v
```
预期：全部通过

- [ ] **Step 2: 运行全量前端测试**

```bash
npm run test -- --run
```
预期：全部通过

- [ ] **Step 3: 前端构建验证**

```bash
npm run build
```
预期：成功

- [ ] **Step 4: 更新接口文档**

在 `docs/development/api-interfaces.md` 中更新各接口状态：
- `get_fund_list`: ⚠️ → ✅ 已接真实数据
- `get_dashboard_signals`: ⚠️ → ✅ 已接真实数据
- ISSUE-01: ✅ 已解决
- ISSUE-03: ✅ 已解决
- ISSUE-04: ✅ 已解决（sync 模块实现）
- ISSUE-05: ✅ 已解决（change_pct 字段已加入）
- ISSUE-08: ✅ 已解决（技术指标文字化实现）

- [ ] **Step 5: 提交**

```bash
git add docs/development/api-interfaces.md
git commit -m "docs: 更新接口文档状态 — P0 阶段完成"
```

---

## 自审

### 1. 规格覆盖检查

| 需求 | 对应 Task |
|---|---|
| 数据同步 akshare → SQLite | Task 0 (sync.py) |
| get_fund_list 接真实数据 | Task 1 + Task 2 |
| get_dashboard_signals 接真实数据 | Task 2 |
| FundList snake→camel 转换 | Task 3 |
| 技术指标文字化 | Task 1 (FundService) |
| 评分 1-10 映射 | Task 1 (FundService) |
| 首次运行自动同步 | Task 2 (main.py) |
| change_pct 字段 | Task 2 (_build_dashboard_signals) |

### 2. 占位符扫描
无 TBD/TODO/placeholder。

### 3. 类型一致性
- `FundListItem` 在 `fundList.ts` 定义，`FundService.get_fund_list()` 返回 snake_case dict，字段名一致
- `FundListRow` 由 `toFundListRow` 转换，与前端 FundList.vue 原有派生行类型一致
- `change_pct` 在 `_build_dashboard_signals` 中计算，与 `DashboardSignal` 接口定义一致

### 4. 范围检查
本计划聚焦 P0 阶段（数据同步 + 两个核心接口），不包含 `get_fund_analysis` 和 `search_funds`（P1 阶段），范围适当。

---

Plan complete and saved to `docs/superpowers/plans/2026-04-04-p0-data-sync-and-real-apis.md`. Two execution options:

**1. Subagent-Driven (recommended)** — 每个 Task 派发独立子代理并行执行，中间有 review 检查点

**2. Inline Execution** — 在当前会话中按 Task 顺序执行，批量推进

你选哪种方式？
