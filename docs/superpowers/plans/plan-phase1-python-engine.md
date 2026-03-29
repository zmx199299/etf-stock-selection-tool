# 阶段一：Python 分析引擎 — 实施计划

> **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development or superpowers:executing-plans

**Goal:** 构建可 CLI 独立运行的完整 Python 分析引擎

**任务清单：**

| Task | 内容 | 依赖 |
|------|------|------|
| 3 | SQLite 数据库模型与操作 | Task 2 |
| 4 | 数据源抽象接口 + akshare 实现 | Task 3 |
| 5 | 技术指标计算模块 | Task 3 |
| 6 | 综合评分模块 | Task 5 |
| 7 | 日内形态筛选模块 | Task 5, 6 |
| 8 | 交易成本与资金分配模块 | Task 3 |
| 9 | 配置管理模块 | Task 3 |
| 10 | JSON-RPC 入口与 CLI 模式 | Task 3-9 |
| 11 | 集成测试 | Task 10 |

详细步骤见各 Task 子文件。

---

## Task 3: SQLite 数据库模型与操作

**Files:**
- Create: `src-python/engine/models/database.py`
- Test: `src-python/tests/test_database.py`

- [ ] **Step 1: 编写数据库测试**

```python
# src-python/tests/test_database.py
import os, tempfile, pytest
from engine.models.database import Database

@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    d = Database(path)
    d.init()
    yield d
    d.close()
    os.unlink(path)

def test_init_creates_tables(db):
    tables = db.get_tables()
    assert "fund_info" in tables
    assert "daily_quote" in tables
    assert "config" in tables
    assert "screening_result" in tables
    assert "scoring_result" in tables
    assert "run_log" in tables

def test_upsert_fund_info(db):
    fund = {
        "code": "510300", "name": "沪深300ETF",
        "fund_type": "ETF", "invest_type": "指数型",
        "t_plus": "T+1", "list_date": "2012-05-28",
        "is_excluded": 0
    }
    db.upsert_fund_info([fund])
    result = db.get_fund_info("510300")
    assert result["name"] == "沪深300ETF"
    assert result["invest_type"] == "指数型"

def test_upsert_daily_quote(db):
    quote = {
        "code": "510300", "date": "2026-03-28",
        "open": 3.95, "close": 4.0, "high": 4.05, "low": 3.90,
        "volume": 100000, "amount": 400000,
        "nav": 3.98, "premium_rate": 0.005,
        "prev_close": 3.96, "is_suspended": 0, "suspended_days": 0
    }
    db.upsert_daily_quotes([quote])
    result = db.get_daily_quotes("510300", "2026-03-28", "2026-03-28")
    assert len(result) == 1
    assert result[0]["close"] == 4.0

def test_get_latest_date(db):
    quote = {
        "code": "510300", "date": "2026-03-28",
        "open": 3.95, "close": 4.0, "high": 4.05, "low": 3.90,
        "volume": 100000, "amount": 400000,
        "nav": 3.98, "premium_rate": 0.005,
        "prev_close": 3.96, "is_suspended": 0, "suspended_days": 0
    }
    db.upsert_daily_quotes([quote])
    assert db.get_latest_date("510300") == "2026-03-28"
    assert db.get_latest_date("999999") is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /home/zmx/codelearn/etf-test
source .venv/bin/activate
python -m pytest src-python/tests/test_database.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: 实现 database.py**

```python
# src-python/engine/models/database.py
import sqlite3
from typing import Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def init(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def close(self):
        if self.conn:
            self.conn.close()

    def _create_tables(self):
        c = self.conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS fund_info (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            fund_type TEXT NOT NULL,
            invest_type TEXT NOT NULL,
            t_plus TEXT NOT NULL,
            list_date TEXT,
            is_excluded INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS daily_quote (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL, close REAL, high REAL, low REAL,
            volume REAL, amount REAL,
            nav REAL, premium_rate REAL,
            prev_close REAL,
            is_suspended INTEGER DEFAULT 0,
            suspended_days INTEGER DEFAULT 0,
            PRIMARY KEY (code, date),
            FOREIGN KEY (code) REFERENCES fund_info(code)
        );
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS screening_result (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            score REAL,
            consecutive_days INTEGER,
            passed INTEGER,
            buy_price REAL,
            tp_price REAL, sl_price REAL,
            details TEXT,
            PRIMARY KEY (code, date)
        );
        CREATE TABLE IF NOT EXISTS scoring_result (
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            total_score REAL,
            trend_score REAL, momentum_score REAL,
            volatility_score REAL, volume_score REAL,
            signal TEXT,
            details TEXT,
            PRIMARY KEY (code, date)
        );
        CREATE TABLE IF NOT EXISTS run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase TEXT, start_time TEXT, end_time TEXT,
            fund_count INTEGER, hit_count INTEGER,
            status TEXT, error TEXT
        );
        """)
        self.conn.commit()

    def get_tables(self) -> list[str]:
        c = self.conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [r[0] for r in c.fetchall()]

    def upsert_fund_info(self, funds: list[dict]):
        c = self.conn.cursor()
        for f in funds:
            c.execute("""
                INSERT INTO fund_info (code,name,fund_type,invest_type,t_plus,list_date,is_excluded)
                VALUES (:code,:name,:fund_type,:invest_type,:t_plus,:list_date,:is_excluded)
                ON CONFLICT(code) DO UPDATE SET
                    name=excluded.name, fund_type=excluded.fund_type,
                    invest_type=excluded.invest_type, t_plus=excluded.t_plus,
                    list_date=excluded.list_date, is_excluded=excluded.is_excluded
            """, f)
        self.conn.commit()

    def get_fund_info(self, code: str) -> Optional[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM fund_info WHERE code=?", (code,))
        row = c.fetchone()
        return dict(row) if row else None

    def get_all_active_funds(self) -> list[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM fund_info WHERE is_excluded=0")
        return [dict(r) for r in c.fetchall()]

    def upsert_daily_quotes(self, quotes: list[dict]):
        c = self.conn.cursor()
        for q in quotes:
            c.execute("""
                INSERT INTO daily_quote
                    (code,date,open,close,high,low,volume,amount,
                     nav,premium_rate,prev_close,is_suspended,suspended_days)
                VALUES (:code,:date,:open,:close,:high,:low,:volume,:amount,
                        :nav,:premium_rate,:prev_close,:is_suspended,:suspended_days)
                ON CONFLICT(code,date) DO UPDATE SET
                    open=excluded.open, close=excluded.close,
                    high=excluded.high, low=excluded.low,
                    volume=excluded.volume, amount=excluded.amount,
                    nav=excluded.nav, premium_rate=excluded.premium_rate,
                    prev_close=excluded.prev_close,
                    is_suspended=excluded.is_suspended,
                    suspended_days=excluded.suspended_days
            """, q)
        self.conn.commit()

    def get_daily_quotes(self, code: str, start: str, end: str) -> list[dict]:
        c = self.conn.cursor()
        c.execute(
            "SELECT * FROM daily_quote WHERE code=? AND date>=? AND date<=? ORDER BY date",
            (code, start, end)
        )
        return [dict(r) for r in c.fetchall()]

    def get_latest_date(self, code: str) -> Optional[str]:
        c = self.conn.cursor()
        c.execute("SELECT MAX(date) FROM daily_quote WHERE code=?", (code,))
        row = c.fetchone()
        return row[0] if row and row[0] else None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest src-python/tests/test_database.py -v
```
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/models/ src-python/tests/test_database.py
git commit -m "feat: add SQLite database model with fund_info and daily_quote tables"
```
