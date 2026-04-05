# 分钟线数据获取与存储实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 ETF 分析系统新增分钟线（1分、5分、60分、120分）数据获取、存储、同步和前端查询能力。

**Architecture:** 在现有架构上新增 `minute_quote` 数据库表，扩展 `DataSource` 接口支持分钟线获取，通过 `DataSyncPipeline` 同步数据，新增 `AnalysisService` 将数据库数据转换为前端 `AnalysisPeriod` 格式，通过 JSON-RPC `get_analysis_data` 方法暴露给前端。

**Tech Stack:** Python (akshare, pandas, SQLite), JSON-RPC over stdin/stdout, Vue 3 (前端对接)

---

## 文件结构

| 操作 | 文件路径 | 责任 |
|------|---------|------|
| 修改 | `src-python/engine/data/base.py` | 扩展 `DataSource` 接口，新增 `fetch_minute_quotes` 抽象方法 |
| 修改 | `src-python/engine/data/akshare_source.py` | 实现 `fetch_minute_quotes` 方法 |
| 修改 | `src-python/engine/models/database.py` | 新增 `minute_quote` 表，新增分钟线 CRUD 方法 |
| 修改 | `src-python/engine/sync.py` | 新增 `sync_minute_quotes_for_all` 同步方法 |
| 新建 | `src-python/engine/services/analysis_service.py` | 分析数据服务，将 DB 数据转为前端格式 |
| 修改 | `src-python/engine/server.py` | 在 `create_real_server` 中注册 `get_analysis_data` |
| 修改 | `src-python/main.py` | 导入新增模块 |
| 新建 | `src-python/tests/test_minute_quotes.py` | 分钟线数据获取、存储、同步测试 |
| 新建 | `src-python/tests/test_analysis_service.py` | 分析服务数据转换测试 |

---

### Task 1: 扩展 DataSource 接口

**Files:**
- Modify: `src-python/engine/data/base.py`
- Test: `src-python/tests/test_minute_quotes.py`

- [ ] **Step 1: 编写测试**

```python
# src-python/tests/test_minute_quotes.py
"""分钟线数据获取、存储、同步测试"""
import pytest
from engine.data.base import DataSource


class TestDataSourceInterface:
    """测试 DataSource 接口是否定义了 fetch_minute_quotes"""

    def test_datasource_has_fetch_minute_quotes(self):
        """DataSource 应该有 fetch_minute_quotes 抽象方法"""
        assert hasattr(DataSource, 'fetch_minute_quotes')
        # 尝试实例化会失败，因为是抽象类
        with pytest.raises(TypeError):
            DataSource()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest src-python/tests/test_minute_quotes.py::TestDataSourceInterface -v
```
预期：FAIL（`fetch_minute_quotes` 方法不存在）

- [ ] **Step 3: 修改 base.py 添加抽象方法**

```python
# src-python/engine/data/base.py
# 在现有代码末尾添加：

    @abstractmethod
    def fetch_minute_quotes(self, code: str, period: str) -> list[dict]:
        """获取指定基金的分钟线行情
        Args:
            code: 基金代码
            period: 周期标识 '1', '5', '60'
        Returns:
            [{"datetime": "YYYY-MM-DD HH:MM:SS", "open": float, "close": float,
              "high": float, "low": float, "volume": float, "amount": float}]
        """
        ...
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest src-python/tests/test_minute_quotes.py::TestDataSourceInterface -v
```
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/data/base.py src-python/tests/test_minute_quotes.py
git commit -m "feat: 扩展 DataSource 接口支持分钟线获取"
```

---

### Task 2: 实现 AkshareSource 分钟线获取

**Files:**
- Modify: `src-python/engine/data/akshare_source.py`
- Test: `src-python/tests/test_minute_quotes.py`

- [ ] **Step 1: 编写测试（使用 mock）**

```python
# 添加到 src-python/tests/test_minute_quotes.py

from unittest.mock import patch, MagicMock
from engine.data.akshare_source import AkshareSource


class TestAkshareMinuteQuotes:
    """测试 AkshareSource 分钟线获取"""

    @patch('engine.data.akshare_source.ak')
    def test_fetch_etf_minute_quotes(self, mock_ak):
        """测试 ETF 分钟线获取"""
        import pandas as pd
        # Mock akshare 返回
        mock_df = pd.DataFrame({
            '时间': ['2024-01-15 09:31:00', '2024-01-15 09:32:00'],
            '开盘': [4.10, 4.11],
            '收盘': [4.11, 4.12],
            '最高': [4.12, 4.13],
            '最低': [4.09, 4.10],
            '成交量': [100000, 120000],
            '成交额': [410000, 492000],
        })
        mock_ak.fund_etf_hist_min_em.return_value = mock_df

        source = AkshareSource()
        result = source.fetch_minute_quotes('510300', '5')

        assert len(result) == 2
        assert result[0]['datetime'] == '2024-01-15 09:31:00'
        assert result[0]['open'] == 4.10
        assert result[0]['close'] == 4.11
        assert result[0]['high'] == 4.12
        assert result[0]['low'] == 4.09
        assert result[0]['volume'] == 100000
        assert result[0]['amount'] == 410000

    @patch('engine.data.akshare_source.ak')
    def test_fetch_etf_minute_quotes_empty(self, mock_ak):
        """测试 ETF 分钟线获取返回空数据"""
        import pandas as pd
        mock_ak.fund_etf_hist_min_em.return_value = pd.DataFrame()

        source = AkshareSource()
        result = source.fetch_minute_quotes('510300', '5')

        assert result == []

    @patch('engine.data.akshare_source.ak')
    def test_fetch_etf_minute_quotes_exception(self, mock_ak):
        """测试 ETF 分钟线获取异常处理"""
        mock_ak.fund_etf_hist_min_em.side_effect = Exception("API error")

        source = AkshareSource()
        result = source.fetch_minute_quotes('510300', '5')

        assert result == []

    @patch('engine.data.akshare_source.ak')
    def test_fetch_lof_minute_quotes(self, mock_ak):
        """测试 LOF 分钟线获取"""
        import pandas as pd
        mock_df = pd.DataFrame({
            '时间': ['2024-01-15 09:31:00'],
            '开盘': [1.50],
            '收盘': [1.51],
            '最高': [1.52],
            '最低': [1.49],
            '成交量': [50000],
            '成交额': [75000],
        })
        mock_ak.fund_lof_hist_min_em.return_value = mock_df

        source = AkshareSource()
        result = source.fetch_minute_quotes('162411', '5')

        assert len(result) == 1
        assert result[0]['datetime'] == '2024-01-15 09:31:00'
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest src-python/tests/test_minute_quotes.py::TestAkshareMinuteQuotes -v
```
预期：FAIL（`fetch_minute_quotes` 方法未实现）

- [ ] **Step 3: 实现 fetch_minute_quotes 方法**

```python
# src-python/engine/data/akshare_source.py
# 在文件末尾添加（在类内部）：

    def fetch_minute_quotes(self, code: str, period: str) -> list[dict]:
        """获取指定基金的分钟线行情
        Args:
            code: 基金代码
            period: 周期标识 '1', '5', '60'
        Returns:
            [{"datetime": "YYYY-MM-DD HH:MM:SS", "open": float, "close": float,
              "high": float, "low": float, "volume": float, "amount": float}]
        """
        if period not in ('1', '5', '60'):
            return []

        try:
            # 尝试 ETF 分钟线
            df = ak.fund_etf_hist_min_em(symbol=code, period=period)
        except Exception:
            try:
                # 尝试 LOF 分钟线
                df = ak.fund_lof_hist_min_em(symbol=code, period=period)
            except Exception:
                return []

        if df.empty:
            return []

        results = []
        for _, row in df.iterrows():
            time_str = str(row.get("时间", ""))
            # 标准化时间格式
            if ' ' in time_str:
                datetime_str = time_str[:19]  # "YYYY-MM-DD HH:MM:SS"
            else:
                datetime_str = time_str

            results.append({
                "datetime": datetime_str,
                "open": float(row.get("开盘", 0)),
                "close": float(row.get("收盘", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
            })

        return results
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest src-python/tests/test_minute_quotes.py::TestAkshareMinuteQuotes -v
```
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/data/akshare_source.py src-python/tests/test_minute_quotes.py
git commit -m "feat: 实现 AkshareSource 分钟线获取（ETF/LOF）"
```

---

### Task 3: 新增 minute_quote 数据库表

**Files:**
- Modify: `src-python/engine/models/database.py`
- Test: `src-python/tests/test_minute_quotes.py`

- [ ] **Step 1: 编写测试**

```python
# 添加到 src-python/tests/test_minute_quotes.py

import os
import tempfile
from engine.models.database import Database


class TestMinuteQuoteTable:
    """测试 minute_quote 数据库表"""

    def setup_method(self):
        """每个测试前创建临时数据库"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init()

    def teardown_method(self):
        """每个测试后清理临时数据库"""
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_minute_quote_table_exists(self):
        """测试 minute_quote 表被创建"""
        tables = self.db.get_tables()
        assert 'minute_quote' in tables

    def test_upsert_minute_quotes(self):
        """测试插入分钟线数据"""
        quotes = [
            {
                "code": "510300",
                "datetime": "2024-01-15 09:31:00",
                "period": "5",
                "open": 4.10,
                "close": 4.11,
                "high": 4.12,
                "low": 4.09,
                "volume": 100000,
                "amount": 410000,
            },
            {
                "code": "510300",
                "datetime": "2024-01-15 09:36:00",
                "period": "5",
                "open": 4.11,
                "close": 4.12,
                "high": 4.13,
                "low": 4.10,
                "volume": 120000,
                "amount": 492000,
            },
        ]
        self.db.upsert_minute_quotes(quotes)

        result = self.db.get_minute_quotes("510300", "5", "2024-01-15 00:00:00", "2024-01-15 23:59:59")
        assert len(result) == 2
        assert result[0]["open"] == 4.10
        assert result[1]["close"] == 4.12

    def test_upsert_minute_quotes_duplicate(self):
        """测试 UPSERT 逻辑（重复插入应更新）"""
        quote = {
            "code": "510300",
            "datetime": "2024-01-15 09:31:00",
            "period": "5",
            "open": 4.10,
            "close": 4.11,
            "high": 4.12,
            "low": 4.09,
            "volume": 100000,
            "amount": 410000,
        }
        self.db.upsert_minute_quotes([quote])

        # 更新同一条记录
        quote["close"] = 4.15
        self.db.upsert_minute_quotes([quote])

        result = self.db.get_minute_quotes("510300", "5", "2024-01-15 00:00:00", "2024-01-15 23:59:59")
        assert len(result) == 1
        assert result[0]["close"] == 4.15

    def test_get_latest_minute_datetime(self):
        """测试获取最新时间戳"""
        quotes = [
            {"code": "510300", "datetime": "2024-01-15 09:31:00", "period": "5",
             "open": 4.10, "close": 4.11, "high": 4.12, "low": 4.09, "volume": 100000, "amount": 410000},
            {"code": "510300", "datetime": "2024-01-15 10:31:00", "period": "5",
             "open": 4.11, "close": 4.12, "high": 4.13, "low": 4.10, "volume": 120000, "amount": 492000},
        ]
        self.db.upsert_minute_quotes(quotes)

        latest = self.db.get_latest_minute_datetime("510300", "5")
        assert latest == "2024-01-15 10:31:00"

    def test_get_latest_minute_datetime_empty(self):
        """测试无数据时返回 None"""
        latest = self.db.get_latest_minute_datetime("510300", "5")
        assert latest is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest src-python/tests/test_minute_quotes.py::TestMinuteQuoteTable -v
```
预期：FAIL（表和方法不存在）

- [ ] **Step 3: 修改 database.py 添加表和 CRUD 方法**

```python
# src-python/engine/models/database.py

# 修改 _create_tables 方法，在现有表定义后添加：

        c.executescript("""
        -- ... 现有表定义 ...

        CREATE TABLE IF NOT EXISTS minute_quote (
            code TEXT NOT NULL,
            datetime TEXT NOT NULL,
            period TEXT NOT NULL,
            open REAL, close REAL, high REAL, low REAL,
            volume REAL, amount REAL,
            PRIMARY KEY (code, datetime, period),
            FOREIGN KEY (code) REFERENCES fund_info(code)
        );

        CREATE INDEX IF NOT EXISTS idx_minute_quote_code_period
            ON minute_quote(code, period, datetime);
        """)
```

```python
# 在 database.py 文件末尾添加新方法：

    def upsert_minute_quotes(self, quotes: list[dict]):
        """批量插入或更新分钟线数据"""
        c = self.conn.cursor()
        for q in quotes:
            c.execute("""
                INSERT INTO minute_quote
                    (code, datetime, period, open, close, high, low, volume, amount)
                VALUES
                    (:code, :datetime, :period, :open, :close, :high, :low, :volume, :amount)
                ON CONFLICT(code, datetime, period) DO UPDATE SET
                    open=excluded.open, close=excluded.close,
                    high=excluded.high, low=excluded.low,
                    volume=excluded.volume, amount=excluded.amount
            """, q)
        self.conn.commit()

    def get_minute_quotes(self, code: str, period: str, start: str, end: str) -> list[dict]:
        """查询分钟线数据"""
        c = self.conn.cursor()
        c.execute(
            "SELECT * FROM minute_quote WHERE code=? AND period=? AND datetime>=? AND datetime<=? ORDER BY datetime",
            (code, period, start, end)
        )
        return [dict(r) for r in c.fetchall()]

    def get_latest_minute_datetime(self, code: str, period: str) -> Optional[str]:
        """获取某只基金某周期的最新时间戳"""
        c = self.conn.cursor()
        c.execute(
            "SELECT MAX(datetime) FROM minute_quote WHERE code=? AND period=?",
            (code, period)
        )
        row = c.fetchone()
        return row[0] if row and row[0] else None

    def aggregate_120m_from_60m(self, code: str) -> list[dict]:
        """从 60 分钟线聚合 120 分钟线数据"""
        c = self.conn.cursor()
        c.execute("""
            SELECT
                code,
                CASE
                    WHEN CAST(SUBSTR(datetime, 12, 2) AS INTEGER) < 12 THEN
                        SUBSTR(datetime, 1, 11) || '09:30:00'
                    ELSE
                        SUBSTR(datetime, 1, 11) || '13:00:00'
                END as datetime,
                '120' as period,
                FIRST(open) as open,
                MAX(high) as high,
                MIN(low) as low,
                LAST(close) as close,
                SUM(volume) as volume,
                SUM(amount) as amount
            FROM (
                SELECT *,
                    CASE
                        WHEN CAST(SUBSTR(datetime, 12, 2) AS INTEGER) < 12 THEN 'AM'
                        ELSE 'PM'
                    END as session
                FROM minute_quote
                WHERE code = ? AND period = '60'
            )
            GROUP BY code, SUBSTR(datetime, 1, 10), session
            ORDER BY datetime
        """, (code,))

        results = []
        for row in c.fetchall():
            results.append({
                "code": row[0],
                "datetime": row[1],
                "period": row[2],
                "open": row[3],
                "close": row[4],
                "high": row[5],
                "low": row[6],
                "volume": row[7],
                "amount": row[8],
            })
        return results
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest src-python/tests/test_minute_quotes.py::TestMinuteQuoteTable -v
```
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/models/database.py src-python/tests/test_minute_quotes.py
git commit -m "feat: 新增 minute_quote 表和 CRUD 方法"
```

---

### Task 4: 扩展同步管道

**Files:**
- Modify: `src-python/engine/sync.py`
- Test: `src-python/tests/test_minute_quotes.py`

- [ ] **Step 1: 编写测试**

```python
# 添加到 src-python/tests/test_minute_quotes.py

from engine.sync import DataSyncPipeline
from unittest.mock import MagicMock


class TestMinuteQuoteSync:
    """测试分钟线同步管道"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init()

        # 创建 mock 数据源
        self.mock_source = MagicMock(spec=DataSource)

        self.pipeline = DataSyncPipeline(self.db, self.mock_source)

    def teardown_method(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_sync_minute_quotes_for_all(self):
        """测试分钟线同步"""
        # 先插入基金信息
        self.db.upsert_fund_info([{
            "code": "510300",
            "name": "测试ETF",
            "fund_type": "ETF",
            "invest_type": "指数型",
            "t_plus": "T+1",
            "list_date": "2020-01-01",
            "is_excluded": 0,
            "has_market_data": 1,
        }])

        # Mock 分钟线数据
        self.mock_source.fetch_minute_quotes.return_value = [
            {"datetime": "2024-01-15 09:31:00", "open": 4.10, "close": 4.11,
             "high": 4.12, "low": 4.09, "volume": 100000, "amount": 410000},
        ]

        total = self.pipeline.sync_minute_quotes_for_all(periods=['5'])

        assert total == 1
        quotes = self.db.get_minute_quotes("510300", "5", "2024-01-15 00:00:00", "2024-01-15 23:59:59")
        assert len(quotes) == 1

    def test_sync_minute_quotes_empty_response(self):
        """测试空响应不中断同步"""
        self.db.upsert_fund_info([{
            "code": "510300", "name": "测试ETF", "fund_type": "ETF",
            "invest_type": "指数型", "t_plus": "T+1", "list_date": "2020-01-01",
            "is_excluded": 0, "has_market_data": 1,
        }])

        self.mock_source.fetch_minute_quotes.return_value = []

        total = self.pipeline.sync_minute_quotes_for_all(periods=['5'])
        assert total == 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest src-python/tests/test_minute_quotes.py::TestMinuteQuoteSync -v
```
预期：FAIL（`sync_minute_quotes_for_all` 方法不存在）

- [ ] **Step 3: 实现同步方法**

```python
# src-python/engine/sync.py
# 在 DataSyncPipeline 类中添加：

    def sync_minute_quotes_for_all(self, periods: list[str] = None) -> int:
        """同步所有基金的分钟线数据
        Args:
            periods: 需要同步的周期列表，默认 ['1', '5', '60']
        Returns:
            同步的总条数
        """
        if periods is None:
            periods = ['1', '5', '60']

        funds = self.db.get_all_funds_with_market_data()
        total = 0

        for fund in funds:
            code = fund["code"]
            for period in periods:
                try:
                    quotes = self.source.fetch_minute_quotes(code, period)
                    if not quotes:
                        continue

                    # 添加 code 和 period 字段
                    for q in quotes:
                        q["code"] = code
                        q["period"] = period

                    self.db.upsert_minute_quotes(quotes)
                    total += len(quotes)
                except Exception as e:
                    logger.warning(f"Failed to sync {period}m quotes for {code}: {e}")
                    continue

        # 聚合 120 分钟线
        for fund in funds:
            try:
                quotes_120m = self.db.aggregate_120m_from_60m(fund["code"])
                if quotes_120m:
                    self.db.upsert_minute_quotes(quotes_120m)
                    total += len(quotes_120m)
            except Exception as e:
                logger.warning(f"Failed to aggregate 120m for {fund['code']}: {e}")
                continue

        logger.info(f"Synced {total} minute quotes for {len(funds)} funds")
        return total
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest src-python/tests/test_minute_quotes.py::TestMinuteQuoteSync -v
```
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/sync.py src-python/tests/test_minute_quotes.py
git commit -m "feat: 扩展同步管道支持分钟线数据同步"
```

---

### Task 5: 创建 AnalysisService 分析数据服务

**Files:**
- Create: `src-python/engine/services/analysis_service.py`
- Test: `src-python/tests/test_analysis_service.py`

- [ ] **Step 1: 编写测试**

```python
# src-python/tests/test_analysis_service.py
"""分析数据服务测试：将数据库数据转换为前端 AnalysisPeriod 格式"""
import os
import tempfile
import pytest
from engine.models.database import Database
from engine.scoring.indicators import TechnicalIndicators
from engine.services.analysis_service import AnalysisService


class TestAnalysisService:
    """测试分析数据服务"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init()
        self.indicators = TechnicalIndicators()
        self.service = AnalysisService(self.db, self.indicators)

        # 插入测试基金
        self.db.upsert_fund_info([{
            "code": "510300",
            "name": "沪深300ETF",
            "fund_type": "ETF",
            "invest_type": "指数型",
            "t_plus": "T+1",
            "list_date": "2020-01-01",
            "is_excluded": 0,
            "has_market_data": 1,
        }])

    def teardown_method(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def _insert_test_daily_quotes(self):
        """插入测试日线数据"""
        quotes = []
        base_price = 4.00
        for i in range(30):
            date = f"2024-01-{i+1:02d}"
            open_p = base_price + i * 0.02
            close_p = base_price + i * 0.02 + 0.01
            quotes.append({
                "code": "510300",
                "date": date,
                "open": open_p,
                "close": close_p,
                "high": close_p + 0.02,
                "low": open_p - 0.02,
                "volume": 1000000 + i * 10000,
                "amount": (open_p + close_p) * 500000,
                "nav": None,
                "premium_rate": None,
                "prev_close": None,
                "is_suspended": 0,
                "suspended_days": 0,
            })
        self.db.upsert_daily_quotes(quotes)

    def _insert_test_minute_quotes(self):
        """插入测试分钟线数据"""
        quotes = []
        base_price = 4.10
        for i in range(20):
            hour = 9 + (i * 5 + 31) // 60
            minute = (i * 5 + 31) % 60
            if hour >= 11 and minute >= 30:
                hour = 13
                minute = (i * 5 + 31 - 120) % 60
            datetime_str = f"2024-01-15 {hour:02d}:{minute:02d}:00"
            quotes.append({
                "code": "510300",
                "datetime": datetime_str,
                "period": "5",
                "open": base_price + i * 0.01,
                "close": base_price + i * 0.01 + 0.005,
                "high": base_price + i * 0.01 + 0.015,
                "low": base_price + i * 0.01 - 0.005,
                "volume": 50000 + i * 1000,
                "amount": (base_price + i * 0.01) * 50000,
            })
        self.db.upsert_minute_quotes(quotes)

    def test_get_day_period(self):
        """测试获取日线周期数据"""
        self._insert_test_daily_quotes()
        period = self.service.get_day_period("510300")

        assert period["key"] == "day"
        assert period["label"] == "日K"
        assert len(period["candles"]) > 0
        assert len(period["volumes"]) > 0
        assert len(period["timeAxis"]) > 0
        assert len(period["priceAxis"]) > 0
        # 检查 candles 格式 [open, high, low, close]
        candle = period["candles"][0]
        assert len(candle) == 4

    def test_get_minute_period(self):
        """测试获取分钟线周期数据"""
        self._insert_test_minute_quotes()
        period = self.service.get_minute_period("510300", "m5", "5")

        assert period["key"] == "m5"
        assert period["label"] == "5分"
        assert len(period["candles"]) > 0
        assert len(period["volumes"]) > 0

    def test_get_intraday_period(self):
        """测试获取分时数据"""
        self._insert_test_minute_quotes()
        period = self.service.get_intraday_period("510300")

        assert period["key"] == "intraday"
        assert period["label"] == "分时"
        assert len(period["linePoints"]) > 0
        assert len(period["avgLinePoints"]) > 0
        assert period["candles"] == []  # 分时图不使用 candles

    def test_get_analysis_data(self):
        """测试获取完整分析数据"""
        self._insert_test_daily_quotes()
        self._insert_test_minute_quotes()

        result = self.service.get_analysis_data("510300")

        assert result["code"] == "510300"
        assert result["name"] == "沪深300ETF"
        assert "periods" in result
        assert "day" in result["periods"]
        assert "m5" in result["periods"]

    def test_get_analysis_data_not_found(self):
        """测试基金不存在时返回 None"""
        result = self.service.get_analysis_data("999999")
        assert result is None

    def test_metrics_generation(self):
        """测试技术指标生成"""
        self._insert_test_daily_quotes()
        period = self.service.get_day_period("510300")

        assert "metrics" in period
        assert len(period["metrics"]) > 0
        # 检查指标格式
        metric = period["metrics"][0]
        assert "label" in metric
        assert "value" in metric
        assert "summary" in metric
        assert "tone" in metric
        assert metric["tone"] in ("bullish", "neutral", "bearish")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest src-python/tests/test_analysis_service.py -v
```
预期：FAIL（模块不存在）

- [ ] **Step 3: 实现 AnalysisService**

```python
# src-python/engine/services/analysis_service.py
"""分析数据服务：将数据库数据转换为前端 AnalysisPeriod 格式"""
import pandas as pd
from typing import Optional
from engine.models.database import Database
from engine.scoring.indicators import TechnicalIndicators


# 周期标签映射
PERIOD_LABELS = {
    "intraday": "分时",
    "day": "日K",
    "m5": "5分",
    "m60": "60分",
    "m120": "120分",
    "week": "周K",
    "month": "月K",
    "quarter": "季K",
    "year": "年K",
}


class AnalysisService:
    """分析数据服务"""

    def __init__(self, db: Database, indicators: TechnicalIndicators):
        self.db = db
        self.indicators = indicators

    def get_analysis_data(self, code: str) -> Optional[dict]:
        """获取指定基金的完整分析数据"""
        fund = self.db.get_fund_info(code)
        if not fund:
            return None

        # 获取最新日线数据用于基础信息
        quotes = self.db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
        if not quotes:
            return None

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        current_price = float(latest["close"])
        prev_close = float(prev["close"])
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close != 0 else 0.0

        nav = float(latest.get("nav", 0)) if pd.notna(latest.get("nav")) else None
        premium_rate = float(latest.get("premium_rate", 0)) * 100 if pd.notna(latest.get("premium_rate")) else None

        return {
            "code": code,
            "name": fund["name"],
            "market": "SH" if code.startswith(("51", "58", "56")) else "SZ",
            "price": f"{current_price:.3f}",
            "change": f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%",
            "iopv": f"{nav:.3f}" if nav else "N/A",
            "premium": f"{'+' if premium_rate and premium_rate >= 0 else ''}{premium_rate:.2f}%" if premium_rate is not None else "N/A",
            "riskLevel": self._estimate_risk_level(df),
            "strategy": self._generate_strategy(df),
            "periods": {
                "intraday": self.get_intraday_period(code),
                "day": self.get_day_period(code),
                "m5": self.get_minute_period(code, "m5", "5"),
                "m60": self.get_minute_period(code, "m60", "60"),
                "m120": self.get_minute_period(code, "m120", "120"),
                "week": self.get_aggregated_period(code, "week"),
                "month": self.get_aggregated_period(code, "month"),
                "quarter": self.get_aggregated_period(code, "quarter"),
                "year": self.get_aggregated_period(code, "year"),
            },
        }

    def get_day_period(self, code: str) -> dict:
        """获取日线周期数据"""
        quotes = self.db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
        if not quotes:
            return self._empty_period("day")

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        # 取最近 60 条
        df = df.tail(60)

        candles = df[["open", "high", "low", "close"]].values.tolist()
        volumes = df["volume"].tolist()
        time_axis = [d[-5:] for d in df["date"].tolist()]  # MM-DD
        price_axis = self._calc_price_axis(df)
        metrics = self._calc_metrics(df)

        return {
            "key": "day",
            "label": PERIOD_LABELS["day"],
            "summary": f"日线数据显示最近 {len(df)} 个交易日走势",
            "chartHeadline": f"日线趋势观察",
            "chartSummary": f"基于 {len(df)} 个交易日的数据分析",
            "priceAxis": price_axis,
            "timeAxis": time_axis,
            "linePoints": df["close"].tolist(),
            "avgLinePoints": df["close"].rolling(5).mean().fillna(method="bfill").tolist(),
            "candles": candles,
            "volumes": volumes,
            "metrics": metrics,
        }

    def get_minute_period(self, code: str, key: str, period: str) -> dict:
        """获取分钟线周期数据"""
        quotes = self.db.get_minute_quotes(code, period, "2000-01-01 00:00:00", "2099-12-31 23:59:59")
        if not quotes:
            return self._empty_period(key)

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("datetime").reset_index(drop=True)

        # 取最近 120 条
        df = df.tail(120)

        candles = df[["open", "high", "low", "close"]].values.tolist()
        volumes = df["volume"].tolist()
        time_axis = [d[11:16] for d in df["datetime"].tolist()]  # HH:MM
        price_axis = self._calc_price_axis(df)
        metrics = self._calc_metrics(df)

        return {
            "key": key,
            "label": PERIOD_LABELS[key],
            "summary": f"{PERIOD_LABELS[key]}数据显示最近 {len(df)} 根K线走势",
            "chartHeadline": f"{PERIOD_LABELS[key]}趋势观察",
            "chartSummary": f"基于 {len(df)} 根K线的数据分析",
            "priceAxis": price_axis,
            "timeAxis": time_axis,
            "linePoints": df["close"].tolist(),
            "avgLinePoints": df["close"].rolling(5).mean().fillna(method="bfill").tolist(),
            "candles": candles,
            "volumes": volumes,
            "metrics": metrics,
        }

    def get_intraday_period(self, code: str) -> dict:
        """获取分时数据（当日 1 分钟线）"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        start = f"{today} 00:00:00"
        end = f"{today} 23:59:59"

        quotes = self.db.get_minute_quotes(code, "1", start, end)
        if not quotes:
            return self._empty_period("intraday")

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("datetime").reset_index(drop=True)

        line_points = df["close"].tolist()
        # 均价线 = 累计成交额 / 累计成交量
        df["cum_amount"] = df["amount"].cumsum()
        df["cum_volume"] = df["volume"].cumsum()
        avg_line_points = (df["cum_amount"] / df["cum_volume"].replace(0, float("nan"))).fillna(method="ffill").tolist()

        time_axis = [d[11:16] for d in df["datetime"].tolist()]
        price_axis = self._calc_price_axis(df)

        return {
            "key": "intraday",
            "label": PERIOD_LABELS["intraday"],
            "summary": f"分时数据显示当日 {len(df)} 个分钟走势",
            "chartHeadline": "分时价格走势",
            "chartSummary": f"基于当日 {len(df)} 根 1 分钟K线",
            "priceAxis": price_axis,
            "timeAxis": time_axis,
            "linePoints": line_points,
            "avgLinePoints": avg_line_points,
            "candles": [],  # 分时图不使用 K 线
            "volumes": df["volume"].tolist(),
            "metrics": self._calc_intraday_metrics(df),
        }

    def get_aggregated_period(self, code: str, key: str) -> dict:
        """获取聚合周期数据（周/月/季/年）"""
        quotes = self.db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
        if not quotes:
            return self._empty_period(key)

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        # 按周期聚合
        df["date"] = pd.to_datetime(df["date"])
        if key == "week":
            df["period_key"] = df["date"].dt.to_period("W")
        elif key == "month":
            df["period_key"] = df["date"].dt.to_period("M")
        elif key == "quarter":
            df["period_key"] = df["date"].dt.to_period("Q")
        elif key == "year":
            df["period_key"] = df["date"].dt.to_period("Y")
        else:
            return self._empty_period(key)

        agg_df = df.groupby("period_key").agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            amount=("amount", "sum"),
        ).reset_index()

        # 取最近 60 条
        agg_df = agg_df.tail(60)

        candles = agg_df[["open", "high", "low", "close"]].values.tolist()
        volumes = agg_df["volume"].tolist()

        if key == "week":
            time_axis = [f"第{i+1}周" for i in range(len(agg_df))]
        elif key == "month":
            time_axis = [str(p)[:7] for p in agg_df["period_key"]]
        elif key == "quarter":
            time_axis = [f"Q{p.quarter}" for p in agg_df["period_key"]]
        elif key == "year":
            time_axis = [str(p.year) for p in agg_df["period_key"]]
        else:
            time_axis = []

        price_axis = self._calc_price_axis(agg_df)
        metrics = self._calc_metrics(agg_df)

        return {
            "key": key,
            "label": PERIOD_LABELS[key],
            "summary": f"{PERIOD_LABELS[key]}数据显示最近 {len(agg_df)} 个周期走势",
            "chartHeadline": f"{PERIOD_LABELS[key]}趋势观察",
            "chartSummary": f"基于 {len(agg_df)} 个{PERIOD_LABELS[key]}的数据分析",
            "priceAxis": price_axis,
            "timeAxis": time_axis,
            "linePoints": agg_df["close"].tolist(),
            "avgLinePoints": agg_df["close"].rolling(5).mean().fillna(method="bfill").tolist(),
            "candles": candles,
            "volumes": volumes,
            "metrics": metrics,
        }

    def _empty_period(self, key: str) -> dict:
        """返回空周期数据"""
        return {
            "key": key,
            "label": PERIOD_LABELS.get(key, key),
            "summary": "暂无数据",
            "chartHeadline": "数据加载中",
            "chartSummary": "该周期暂无可用数据",
            "priceAxis": [],
            "timeAxis": [],
            "linePoints": [],
            "avgLinePoints": [],
            "candles": [],
            "volumes": [],
            "metrics": [],
        }

    def _calc_price_axis(self, df: pd.DataFrame) -> list[str]:
        """计算价格轴刻度"""
        if df.empty:
            return []
        min_val = df[["low", "open", "close"]].min().min()
        max_val = df[["high", "open", "close"]].max().max()
        if min_val == max_val:
            min_val -= 0.01
            max_val += 0.01
        step = (max_val - min_val) / 4
        return [f"{min_val + i * step:.2f}" for i in range(5)]

    def _calc_metrics(self, df: pd.DataFrame) -> list[dict]:
        """计算技术指标"""
        if len(df) < 20:
            return [{"label": "数据不足", "value": "N/A", "summary": "数据量不足以计算指标", "tone": "neutral"}]

        df_copy = df.copy()
        df_copy = self.indicators.compute_all(df_copy)

        latest = df_copy.iloc[-1]
        metrics = []

        # MACD
        if pd.notna(latest.get("macd_hist")):
            macd_val = latest["macd_hist"]
            if macd_val > 0:
                metrics.append({"label": "MACD", "value": "金叉", "summary": "短线动能转强", "tone": "bullish"})
            elif macd_val < 0:
                metrics.append({"label": "MACD", "value": "死叉", "summary": "短线动能转弱", "tone": "bearish"})
            else:
                metrics.append({"label": "MACD", "value": "粘合", "summary": "多空平衡", "tone": "neutral"})

        # RSI
        if pd.notna(latest.get("rsi6")):
            rsi = latest["rsi6"]
            if rsi > 70:
                metrics.append({"label": "RSI", "value": f"{rsi:.0f}", "summary": "接近超买区域", "tone": "bearish"})
            elif rsi < 30:
                metrics.append({"label": "RSI", "value": f"{rsi:.0f}", "summary": "接近超卖区域", "tone": "bullish"})
            else:
                metrics.append({"label": "RSI", "value": f"{rsi:.0f}", "summary": "中性区域", "tone": "neutral"})

        # BOLL
        if pd.notna(latest.get("boll_mid")):
            close = latest["close"]
            if close > latest["boll_upper"]:
                metrics.append({"label": "BOLL", "value": "突破上轨", "summary": "价格强势突破", "tone": "bullish"})
            elif close < latest["boll_lower"]:
                metrics.append({"label": "BOLL", "value": "跌破下轨", "summary": "价格弱势突破", "tone": "bearish"})
            else:
                metrics.append({"label": "BOLL", "value": "通道内", "summary": "价格在通道内运行", "tone": "neutral"})

        # 均线
        if pd.notna(latest.get("ma5")) and pd.notna(latest.get("ma20")):
            if latest["ma5"] > latest["ma20"]:
                metrics.append({"label": "均线", "value": "多头排列", "summary": "短期趋势向上", "tone": "bullish"})
            else:
                metrics.append({"label": "均线", "value": "空头排列", "summary": "短期趋势向下", "tone": "bearish"})

        return metrics if metrics else [{"label": "指标", "value": "N/A", "summary": "暂无信号", "tone": "neutral"}]

    def _calc_intraday_metrics(self, df: pd.DataFrame) -> list[dict]:
        """计算分时指标"""
        if df.empty:
            return []

        latest = df.iloc[-1]
        first = df.iloc[0]
        change = (latest["close"] - first["open"]) / first["open"] * 100 if first["open"] != 0 else 0

        metrics = []
        if change > 0.5:
            metrics.append({"label": "分时强度", "value": "偏强", "summary": f"当日涨幅 {change:.2f}%", "tone": "bullish"})
        elif change < -0.5:
            metrics.append({"label": "分时强度", "value": "偏弱", "summary": f"当日跌幅 {abs(change):.2f}%", "tone": "bearish"})
        else:
            metrics.append({"label": "分时强度", "value": "平稳", "summary": f"当日波动 {abs(change):.2f}%", "tone": "neutral"})

        return metrics

    def _estimate_risk_level(self, df: pd.DataFrame) -> str:
        """估算风险等级"""
        if len(df) < 20:
            return "数据不足"

        df_copy = df.copy()
        df_copy = self.indicators.compute_all(df_copy)
        atr = df_copy.iloc[-1].get("atr14", 0)
        if pd.isna(atr):
            return "中等波动"

        close = df_copy.iloc[-1]["close"]
        atr_pct = atr / close * 100 if close > 0 else 0

        if atr_pct < 1:
            return "低波动"
        elif atr_pct < 2:
            return "中等波动"
        elif atr_pct < 3:
            return "中高波动"
        else:
            return "高波动"

    def _generate_strategy(self, df: pd.DataFrame) -> dict:
        """生成策略建议"""
        if len(df) < 20:
            return {
                "conclusion": "数据不足，暂无法生成策略",
                "buyZone": "N/A",
                "sellZone": "N/A",
                "position": "观望",
                "stopLoss": "N/A",
                "holdingPeriod": "N/A",
                "riskNote": "数据量不足，建议等待更多数据积累",
            }

        df_copy = df.copy()
        df_copy = self.indicators.compute_all(df_copy)
        latest = df_copy.iloc[-1]

        # 简单策略逻辑
        bullish_signals = 0
        if pd.notna(latest.get("macd_hist")) and latest["macd_hist"] > 0:
            bullish_signals += 1
        if pd.notna(latest.get("rsi6")) and 30 < latest["rsi6"] < 70:
            bullish_signals += 1
        if pd.notna(latest.get("ma5")) and pd.notna(latest.get("ma20")) and latest["ma5"] > latest["ma20"]:
            bullish_signals += 1

        current_price = latest["close"]

        if bullish_signals >= 2:
            conclusion = "趋势偏多，可关注回踩机会"
            position = "建议 3-5 成仓位"
            buy_zone = f"{current_price * 0.98:.2f} - {current_price * 0.99:.2f}"
            sell_zone = f"{current_price * 1.03:.2f} - {current_price * 1.05:.2f}"
            stop_loss = f"{current_price * 0.96:.2f}"
        elif bullish_signals == 1:
            conclusion = "多空平衡，等待方向确认"
            position = "建议 1-3 成试探仓位"
            buy_zone = f"{current_price * 0.97:.2f} - {current_price * 0.98:.2f}"
            sell_zone = f"{current_price * 1.02:.2f} - {current_price * 1.04:.2f}"
            stop_loss = f"{current_price * 0.95:.2f}"
        else:
            conclusion = "趋势偏空，建议观望"
            position = "建议空仓或极轻仓位"
            buy_zone = f"{current_price * 0.95:.2f} - {current_price * 0.97:.2f}"
            sell_zone = f"{current_price * 1.01:.2f} - {current_price * 1.03:.2f}"
            stop_loss = f"{current_price * 0.93:.2f}"

        return {
            "conclusion": conclusion,
            "buyZone": buy_zone,
            "sellZone": sell_zone,
            "position": position,
            "stopLoss": f"跌破 {stop_loss} 止损",
            "holdingPeriod": "3-10 个交易日",
            "riskNote": "以上为系统自动分析，仅供参考",
        }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest src-python/tests/test_analysis_service.py -v
```
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/services/analysis_service.py src-python/tests/test_analysis_service.py
git commit -m "feat: 创建 AnalysisService 分析数据服务"
```

---

### Task 6: 注册 JSON-RPC 方法

**Files:**
- Modify: `src-python/engine/server.py`
- Modify: `src-python/main.py`
- Test: `src-python/tests/test_analysis_service.py`（端到端测试）

- [ ] **Step 1: 修改 server.py 注册方法**

```python
# src-python/engine/server.py
# 修改 create_real_server 函数：

def create_real_server(db, source):
    """创建使用真实模块的 JSONRPCServer"""
    import pandas as pd
    from engine.services.fund_service import FundService
    from engine.scoring.indicators import TechnicalIndicators
    from engine.scoring.scorer import Scorer
    from engine.sync import DataSyncPipeline
    from engine.services.analysis_service import AnalysisService

    server = JSONRPCServer()

    # 初始化组件
    indicators = TechnicalIndicators()
    scorer = Scorer()
    fund_service = FundService(db, indicators, scorer)
    sync_pipeline = DataSyncPipeline(db, source)
    analysis_service = AnalysisService(db, indicators)

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

    def get_analysis_data_real(code: str):
        return analysis_service.get_analysis_data(code)

    server.register_method("get_analysis_data", get_analysis_data_real)

    return server
```

- [ ] **Step 2: 修改 main.py 导入**

```python
# src-python/main.py
# 无需额外修改，因为 create_real_server 在 server.py 内部处理导入
```

- [ ] **Step 3: 运行全量测试**

```bash
pytest src-python/tests/ -v
```
预期：所有测试 PASS

- [ ] **Step 4: 提交**

```bash
git add src-python/engine/server.py src-python/main.py
git commit -m "feat: 注册 get_analysis_data JSON-RPC 方法"
```

---

### Task 7: 运行全量测试验证

**Files:**
- Test: `src-python/tests/`

- [ ] **Step 1: 运行所有 Python 测试**

```bash
pytest src-python/tests/ -v
```
预期：所有测试 PASS

- [ ] **Step 2: 运行前端构建验证**

```bash
npm run build
```
预期：构建成功（TypeScript 类型检查通过）

- [ ] **Step 3: 提交（如有变更）**

```bash
git add .
git commit -m "test: 全量测试验证通过"
```

---

## 自审清单

- [x] 所有需求在 spec 中都有对应任务实现
- [x] 无 "TBD"、"TODO" 等占位符
- [x] 类型签名和方法名在各任务间保持一致
- [x] 每个步骤包含完整代码和命令
- [x] 测试覆盖数据获取、存储、同步、服务转换全链路
- [x] 前端数据格式与 `AnalysisPeriod` 类型完全匹配
