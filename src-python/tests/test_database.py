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
        "code": "510300", "name": "沪深300ETF",
        "fund_type": "ETF", "invest_type": "指数型",
        "t_plus": "T+1", "list_date": "2012-05-28",
        "is_excluded": 0, "has_market_data": 1
    }
    db.upsert_fund_info([fund])
    result = db.get_fund_info("510300")
    assert result is not None
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

def test_update_has_market_data_rejects_invalid_values(db):
    fund = {
        "code": "160137", "name": "互联基金",
        "fund_type": "LOF", "invest_type": "指数型",
        "t_plus": "T+1", "list_date": "",
        "is_excluded": 0, "has_market_data": 1,
    }
    db.upsert_fund_info([fund])
    with pytest.raises(ValueError, match="has_market_data must be 0 or 1"):
        db.update_has_market_data("160137", 2)
    with pytest.raises(ValueError, match="has_market_data must be 0 or 1"):
        db.update_has_market_data("160137", -1)
