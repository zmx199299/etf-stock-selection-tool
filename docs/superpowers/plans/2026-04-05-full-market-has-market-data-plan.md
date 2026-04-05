# 全量库严格全量 + 标记隔离 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `fund_info` 表中新增 `has_market_data` 字段，使同步脚本能标记无场内交易行情的 LOF 基金，导入过程不再因单只基金缺失行情而中断，最终产出包含全量 1753 只基金的种子数据库。

**Architecture:** 在数据库层新增字段和查询方法 → 在种子同步层根据新浪分类页的成交量/最新价预判标记 → 在同步脚本中跳过无行情基金的行情拉取 → 全量测试验证。

**Tech Stack:** Python 3, SQLite, akshare, pytest

---

### Task 1: 数据库层新增 `has_market_data` 字段

**Files:**
- Modify: `src-python/engine/models/database.py`
- Test: `src-python/tests/test_database.py`

- [ ] **Step 1: Write failing tests for `has_market_data`**

Add to `src-python/tests/test_database.py`:

```python
def test_fund_info_has_market_data_field(db):
    fund = {
        "code": "510300", "name": "沪深300ETF",
        "fund_type": "ETF", "invest_type": "指数型",
        "t_plus": "T+1", "list_date": "2012-05-28",
        "is_excluded": 0, "has_market_data": 1,
    }
    db.upsert_fund_info([fund])
    result = db.get_fund_info("510300")
    assert result is not None
    assert result["has_market_data"] == 1

def test_get_all_funds_with_market_data(db):
    funds = [
        {"code": "510300", "name": "沪深300ETF", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "", "is_excluded": 0, "has_market_data": 1},
        {"code": "160137", "name": "互联基金", "fund_type": "LOF", "invest_type": "指数型", "t_plus": "T+1", "list_date": "", "is_excluded": 0, "has_market_data": 0},
    ]
    db.upsert_fund_info(funds)
    with_market = db.get_all_funds_with_market_data()
    codes = [f["code"] for f in with_market]
    assert "510300" in codes
    assert "160137" not in codes

def test_update_has_market_data(db):
    fund = {
        "code": "160137", "name": "互联基金",
        "fund_type": "LOF", "invest_type": "指数型",
        "t_plus": "T+1", "list_date": "",
        "is_excluded": 0, "has_market_data": 1,
    }
    db.upsert_fund_info([fund])
    db.update_has_market_data("160137", 0)
    result = db.get_fund_info("160137")
    assert result["has_market_data"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest src-python/tests/test_database.py -v`
Expected: 3 new tests fail with SQL errors (column `has_market_data` does not exist, method `get_all_funds_with_market_data` not defined, method `update_has_market_data` not defined)

- [ ] **Step 3: Modify `_create_tables()` to add `has_market_data`**

In `src-python/engine/models/database.py`, modify the `fund_info` table DDL:

```python
CREATE TABLE IF NOT EXISTS fund_info (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    fund_type TEXT NOT NULL,
    invest_type TEXT NOT NULL,
    t_plus TEXT NOT NULL,
    list_date TEXT,
    is_excluded INTEGER DEFAULT 0,
    has_market_data INTEGER DEFAULT 1
);
```

- [ ] **Step 4: Modify `upsert_fund_info()` to include `has_market_data`**

In `src-python/engine/models/database.py`, update the SQL:

```python
def upsert_fund_info(self, funds: list[dict]):
    c = self.conn.cursor()
    for f in funds:
        c.execute("""
            INSERT INTO fund_info (code,name,fund_type,invest_type,t_plus,list_date,is_excluded,has_market_data)
            VALUES (:code,:name,:fund_type,:invest_type,:t_plus,:list_date,:is_excluded,:has_market_data)
            ON CONFLICT(code) DO UPDATE SET
                name=excluded.name, fund_type=excluded.fund_type,
                invest_type=excluded.invest_type, t_plus=excluded.t_plus,
                list_date=excluded.list_date, is_excluded=excluded.is_excluded,
                has_market_data=excluded.has_market_data
        """, f)
    self.conn.commit()
```

- [ ] **Step 5: Add `get_all_funds_with_market_data()` method**

In `src-python/engine/models/database.py`, after `get_all_active_funds()`:

```python
def get_all_funds_with_market_data(self) -> list[dict]:
    c = self.conn.cursor()
    c.execute("SELECT * FROM fund_info WHERE is_excluded=0 AND has_market_data=1")
    return [dict(r) for r in c.fetchall()]
```

- [ ] **Step 6: Add `update_has_market_data()` method**

In `src-python/engine/models/database.py`, at the end of the class:

```python
def update_has_market_data(self, code: str, value: int):
    c = self.conn.cursor()
    c.execute("UPDATE fund_info SET has_market_data=? WHERE code=?", (value, code))
    self.conn.commit()
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest src-python/tests/test_database.py -v`
Expected: All tests PASS (existing + 3 new)

- [ ] **Step 8: Commit**

```bash
git add src-python/engine/models/database.py src-python/tests/test_database.py
git commit -m "feat: add has_market_data field to fund_info for marking LOFs without exchange trading data"
```

---

### Task 2: 种子同步层标记无行情基金

**Files:**
- Modify: `src-python/engine/seed_sync.py`
- Test: `src-python/tests/test_seed_sync.py`

- [ ] **Step 1: Write failing test for `has_market_data` marking**

Add to `src-python/tests/test_seed_sync.py`:

```python
def test_build_full_market_fund_records_marks_zero_volume_funds():
    name_rows = [
        {"基金代码": "161725", "基金简称": "招商中证白酒指数(LOF)A", "基金类型": "指数型-股票"},
        {"基金代码": "160137", "基金简称": "南方中证互联网指数(LOF)A", "基金类型": "指数型-股票"},
    ]
    etf_rows = []
    lof_rows = [
        {"代码": "sz161725", "名称": "招商中证白酒指数LOF", "最新价": 1.5, "成交量": 10000},
        {"代码": "sz160137", "名称": "互联基金", "最新价": 0.0, "成交量": 0},
    ]

    records = build_full_market_fund_records(name_rows, etf_rows, lof_rows)
    record_map = {item["code"]: item for item in records}

    assert record_map["161725"]["has_market_data"] == 1
    assert record_map["160137"]["has_market_data"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest src-python/tests/test_seed_sync.py::test_build_full_market_fund_records_marks_zero_volume_funds -v`
Expected: FAIL with KeyError (`has_market_data` not in record) or assertion error

- [ ] **Step 3: Modify `add_rows()` in `build_full_market_fund_records()` to set `has_market_data`**

In `src-python/engine/seed_sync.py`, inside the `add_rows()` function, after building the record dict, add `has_market_data` logic. The `row` dict from sina category contains `最新价` and `成交量` fields. Modify the record construction:

```python
def add_rows(rows: list[dict], market_label: str):
    for row in rows:
        code = normalize_fund_code(row.get("代码"))
        if not code:
            continue

        market_name = str(row.get("名称", "")).strip()
        meta = name_map.get(code) or fallback_details.get(code)
        if meta is None:
            raise ValueError(f"missing metadata for market fund: {code}")

        raw_fund_type = str(meta.get("fund_type_raw", "")).strip()
        if is_excluded_fund_type(raw_fund_type):
            continue

        name = str(meta.get("name") or market_name).strip()

        latest_price = float(row.get("最新价", 0) or 0)
        volume = float(row.get("成交量", 0) or 0)
        has_market_data = 1 if (latest_price > 0 or volume > 0) else 0

        records_by_code[code] = {
            "code": code,
            "name": name,
            "fund_type": market_label,
            "invest_type": _classifier._classify_invest_type(name),
            "t_plus": _classifier._classify_t_plus(name),
            "list_date": "",
            "is_excluded": 0,
            "has_market_data": has_market_data,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest src-python/tests/test_seed_sync.py -v`
Expected: All tests PASS (existing + 1 new)

- [ ] **Step 5: Commit**

```bash
git add src-python/engine/seed_sync.py src-python/tests/test_seed_sync.py
git commit -m "feat: mark funds with zero volume/price as has_market_data=0 in seed_sync"
```

---

### Task 3: 同步脚本跳过无行情基金

**Files:**
- Modify: `src-python/sync_all.py`
- Test: `src-python/tests/test_sync_all.py`

- [ ] **Step 1: Write failing test for skipping no-market-data funds**

Add to `src-python/tests/test_sync_all.py`:

```python
def test_sync_skips_funds_without_market_data(tmp_path, monkeypatch):
    module = _load_sync_all_module()

    monkeypatch.setattr(
        module,
        "load_name_rows",
        lambda: [
            {"基金代码": "510300", "基金简称": "沪深300ETF华泰柏瑞", "基金类型": "指数型-股票"},
            {"基金代码": "160137", "基金简称": "南方中证互联网指数(LOF)A", "基金类型": "指数型-股票"},
        ],
    )
    monkeypatch.setattr(
        module,
        "load_etf_rows",
        lambda: [{"代码": "sh510300", "名称": "沪深300ETF华泰柏瑞", "最新价": 4.5, "成交量": 10000}],
    )
    monkeypatch.setattr(
        module,
        "load_lof_rows",
        lambda: [{"代码": "sz160137", "名称": "互联基金", "最新价": 0.0, "成交量": 0}],
    )
    monkeypatch.setattr(module, "load_fallback_details", lambda: {})

    fetch_calls = []

    def mock_fetch(code):
        fetch_calls.append(code)
        return [{"code": code, "date": "2026-04-03", "open": 1.0, "close": 1.1, "high": 1.2, "low": 0.9, "volume": 1000.0, "amount": 2000.0, "nav": None, "premium_rate": None, "prev_close": 0.95, "is_suspended": 0, "suspended_days": 0}]

    monkeypatch.setattr(module, "fetch_market_quotes", mock_fetch)
    monkeypatch.setattr(
        module,
        "load_latest_nav_snapshots",
        lambda: {
            "510300": {"date": "2026-04-03", "nav": 4.4499, "premium_rate": 0.0009},
            "160137": {"date": "2026-04-03", "nav": 1.5894, "premium_rate": None},
        },
    )

    db = Database(str(tmp_path / "skip_test.db"))
    db.init()
    try:
        fund_count, quotes_count, nav_count = module.sync_full_market_funds(db)
        assert fund_count == 2
        assert quotes_count == 1
        assert nav_count == 2
        assert fetch_calls == ["510300"]
        assert "160137" not in fetch_calls

        fund_160137 = db.get_fund_info("160137")
        assert fund_160137["has_market_data"] == 0
    finally:
        db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest src-python/tests/test_sync_all.py::test_sync_skips_funds_without_market_data -v`
Expected: FAIL (current code raises RuntimeError for empty quotes or does not skip)

- [ ] **Step 3: Modify `sync_full_market_funds()` to skip no-market-data funds**

In `src-python/sync_all.py`, replace the section 2 loop (lines 96-105) with:

```python
logger.info("[2/3] 拉取全量真实市场日线 OHLC...")
t0 = time.time()
quotes_total = 0
skipped_no_market = 0
for index, fund in enumerate(fund_records, start=1):
    code = fund["code"]
    name = fund["name"]
    if fund.get("has_market_data", 1) == 0:
        logger.info(f"  跳过 {code} {name}（无场内交易行情）")
        skipped_no_market += 1
        continue
    quotes = fetch_market_quotes(code)
    if not quotes:
        logger.warning(f"  警告: {code} {name} 有行情标记但返回空，更新为无行情")
        db.update_has_market_data(code, 0)
        skipped_no_market += 1
        continue
    db.upsert_daily_quotes(quotes)
    quotes_total += len(quotes)
    if index % 100 == 0 or index == len(fund_records):
        logger.info(f"  进度: {index}/{len(fund_records)}，累计 {quotes_total} 条市场日线")
logger.info(f"  完成: {quotes_total} 条市场日线 (跳过 {skipped_no_market} 只无行情基金, 耗时 {time.time() - t0:.1f}s)")
```

- [ ] **Step 4: Update `main()` output to include has_market_data stats**

In `src-python/sync_all.py`, modify the `main()` function to output the new stats. Change the return value of `sync_full_market_funds()` to include the skipped count, then update the final output.

First, change the return statement at the end of `sync_full_market_funds()`:

```python
return len(fund_records), quotes_total, nav_total, skipped_no_market
```

Then update `main()`:

```python
def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH

    logger.info("=" * 60)
    logger.info("FUNDFLOW 全量库初始化工具")
    logger.info("=" * 60)
    logger.info(f"数据库路径: {db_path}")
    logger.info("口径: 全量场内 ETF+LOF（排除货币/债券），内置全量历史日线 + 全量最新净值")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db = Database(db_path)
    db.init()
    try:
        fund_count, quotes_count, nav_count, skipped_count = sync_full_market_funds(db)
    finally:
        db.close()

    with_market = fund_count - skipped_count
    logger.info("=" * 60)
    logger.info("初始化完成")
    logger.info(f"  基金列表: {fund_count} 只（有行情: {with_market}, 无行情: {skipped_count}）")
    logger.info(f"  市场日线: {quotes_count} 条")
    logger.info(f"  最新净值: {nav_count} 条")
    logger.info(f"  数据库大小: {os.path.getsize(db_path) / 1024:.1f} KB")
    logger.info("=" * 60)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest src-python/tests/test_sync_all.py -v`
Expected: All tests PASS (existing + 1 new)

- [ ] **Step 6: Commit**

```bash
git add src-python/sync_all.py src-python/tests/test_sync_all.py
git commit -m "feat: skip no-market-data funds in sync_all and report stats"
```

---

### Task 4: 全量验证 + 文档同步

**Files:**
- Modify: `docs/development/ai/current_state.md`
- Modify: `docs/development/human/2026-04-05-daily-log.md` (create if not exists)

- [ ] **Step 1: Run full Python test suite**

Run: `pytest src-python/tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run frontend build verification**

Run: `npm run build`
Expected: PASS (vue-tsc + vite build)

- [ ] **Step 3: Update AI context state**

Append to `docs/development/ai/current_state.md`:

```markdown
## 全量库严格全量 + 标记隔离 (2026-04-05)

- `fund_info` 表新增 `has_market_data` 字段（DEFAULT 1）
- `build_full_market_fund_records()` 根据新浪分类页的成交量/最新价预判标记
- `sync_all.py` 跳过 `has_market_data=0` 的基金行情拉取，不中断导入
- 新增 `get_all_funds_with_market_data()` 和 `update_has_market_data()` 数据库方法
- 约 22 只 LOF 被标记为 `has_market_data=0`（无场内交易行情）
- 全量 1753 只基金入库，净值全量回填
```

- [ ] **Step 4: Commit**

```bash
git add docs/development/ai/current_state.md
git commit -m "docs: update AI state with has_market_data full-market import design"
```
