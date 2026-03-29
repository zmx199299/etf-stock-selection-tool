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
