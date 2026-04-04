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
    pipeline.sync_fund_list()
    pipeline.sync_daily_quotes_for_all()
    quotes = mock_env["db"].get_daily_quotes("510300", "2026-03-01", "2026-03-28")
    assert len(quotes) == 28
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
    funds = mock_env["db"].get_all_active_funds()
    codes = [f["code"] for f in funds]
    assert "510300" in codes
    assert "513050" in codes
