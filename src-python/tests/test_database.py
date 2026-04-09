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
    assert "fund_nav_history" in tables
    assert "config" in tables
    assert "screening_result" in tables
    assert "scoring_result" in tables
    assert "run_log" in tables


def test_upsert_fund_info(db):
    fund = {
        "code": "510300",
        "name": "沪深300ETF",
        "fund_type": "ETF",
        "invest_type": "指数型",
        "t_plus": "T+1",
        "list_date": "2012-05-28",
        "is_excluded": 0,
        "has_market_data": 1,
    }
    db.upsert_fund_info([fund])
    result = db.get_fund_info("510300")
    assert result is not None
    assert result["name"] == "沪深300ETF"
    assert result["invest_type"] == "指数型"


def test_upsert_daily_quote(db):
    quote = {
        "code": "510300",
        "date": "2026-03-28",
        "open": 3.95,
        "close": 4.0,
        "high": 4.05,
        "low": 3.90,
        "volume": 100000,
        "amount": 400000,
        "nav": 3.98,
        "premium_rate": 0.005,
        "prev_close": 3.96,
        "is_suspended": 0,
        "suspended_days": 0,
    }
    db.upsert_daily_quotes([quote])
    result = db.get_daily_quotes("510300", "2026-03-28", "2026-03-28")
    assert len(result) == 1
    assert result[0]["close"] == 4.0


def test_get_latest_date(db):
    quote = {
        "code": "510300",
        "date": "2026-03-28",
        "open": 3.95,
        "close": 4.0,
        "high": 4.05,
        "low": 3.90,
        "volume": 100000,
        "amount": 400000,
        "nav": 3.98,
        "premium_rate": 0.005,
        "prev_close": 3.96,
        "is_suspended": 0,
        "suspended_days": 0,
    }
    db.upsert_daily_quotes([quote])
    assert db.get_latest_date("510300") == "2026-03-28"
    assert db.get_latest_date("999999") is None


def test_upsert_fund_nav_history_and_query(db):
    rows = [
        {"code": "510300", "date": "2026-03-27", "nav": 4.100},
        {"code": "510300", "date": "2026-03-28", "nav": 4.118},
    ]

    db.upsert_fund_nav_history(rows)

    result = db.get_fund_nav_history("510300", "2026-03-27", "2026-03-28")
    assert len(result) == 2
    assert result[0]["date"] == "2026-03-27"
    assert result[1]["nav"] == pytest.approx(4.118, abs=0.001)


def test_fund_info_has_market_data_field(db):
    fund = {
        "code": "510300",
        "name": "沪深300ETF",
        "fund_type": "ETF",
        "invest_type": "指数型",
        "t_plus": "T+1",
        "list_date": "2012-05-28",
        "is_excluded": 0,
        "has_market_data": 1,
    }
    db.upsert_fund_info([fund])
    result = db.get_fund_info("510300")
    assert result is not None
    assert result["has_market_data"] == 1


def test_get_all_funds_with_market_data(db):
    funds = [
        {
            "code": "510300",
            "name": "沪深300ETF",
            "fund_type": "ETF",
            "invest_type": "指数型",
            "t_plus": "T+1",
            "list_date": "",
            "is_excluded": 0,
            "has_market_data": 1,
        },
        {
            "code": "160137",
            "name": "互联基金",
            "fund_type": "LOF",
            "invest_type": "指数型",
            "t_plus": "T+1",
            "list_date": "",
            "is_excluded": 0,
            "has_market_data": 0,
        },
    ]
    db.upsert_fund_info(funds)
    with_market = db.get_all_funds_with_market_data()
    codes = [f["code"] for f in with_market]
    assert "510300" in codes
    assert "160137" not in codes


def test_update_has_market_data(db):
    fund = {
        "code": "160137",
        "name": "互联基金",
        "fund_type": "LOF",
        "invest_type": "指数型",
        "t_plus": "T+1",
        "list_date": "",
        "is_excluded": 0,
        "has_market_data": 1,
    }
    db.upsert_fund_info([fund])
    db.update_has_market_data("160137", 0)
    result = db.get_fund_info("160137")
    assert result["has_market_data"] == 0


def test_update_has_market_data_rejects_invalid_values(db):
    fund = {
        "code": "160137",
        "name": "互联基金",
        "fund_type": "LOF",
        "invest_type": "指数型",
        "t_plus": "T+1",
        "list_date": "",
        "is_excluded": 0,
        "has_market_data": 1,
    }
    db.upsert_fund_info([fund])
    with pytest.raises(ValueError, match="has_market_data must be 0 or 1"):
        db.update_has_market_data("160137", 2)
    with pytest.raises(ValueError, match="has_market_data must be 0 or 1"):
        db.update_has_market_data("160137", -1)


def test_wal_mode_enabled_after_init(db):
    """init() 后应启用 WAL 模式，允许并发读写"""
    c = db.conn.cursor()
    c.execute("PRAGMA journal_mode")
    mode = c.fetchone()[0]
    assert mode == "wal", f"期望 WAL 模式，实际是 {mode}"


def test_concurrent_writes_no_database_locked(tmp_path):
    """两个连接同时写入同一个 WAL 数据库不应抛出 'database is locked'"""
    import threading

    db_path = str(tmp_path / "concurrent.db")

    # 创建数据库并初始化表结构
    db1 = Database(db_path)
    db1.init()
    db1.upsert_fund_info(
        [
            {
                "code": "510300",
                "name": "沪深300ETF",
                "fund_type": "ETF",
                "invest_type": "指数型",
                "t_plus": "T+1",
                "list_date": "",
                "is_excluded": 0,
            }
        ]
    )

    # 第二个连接（模拟后台同步线程）
    db2 = Database(db_path)
    db2.init()

    errors = []

    def writer(db_instance, code_prefix, count):
        """向 daily_quote 写入 count 条数据"""
        try:
            for i in range(count):
                db_instance.upsert_daily_quotes(
                    [
                        {
                            "code": "510300",
                            "date": f"2026-01-{code_prefix}{i:02d}"[:10],
                            "open": 4.0,
                            "close": 4.1,
                            "high": 4.2,
                            "low": 3.9,
                            "volume": 1000,
                            "amount": 4100,
                            "nav": None,
                            "premium_rate": None,
                            "prev_close": None,
                            "is_suspended": 0,
                            "suspended_days": 0,
                        }
                    ]
                )
        except Exception as e:
            errors.append(str(e))

    t1 = threading.Thread(target=writer, args=(db1, "0", 10))
    t2 = threading.Thread(target=writer, args=(db2, "1", 10))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    db1.close()
    db2.close()

    # 关键断言：不应该有 "database is locked" 错误
    locked_errors = [e for e in errors if "locked" in e.lower()]
    assert locked_errors == [], f"并发写入时出现数据库锁错误: {locked_errors}"
