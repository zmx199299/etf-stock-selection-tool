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
        # 为两只基金都插入足够的日线数据，保证列表查询覆盖完整测试意图
        import numpy as np
        np.random.seed(42)
        n = 30
        dates = pd.date_range(end="2026-03-28", periods=n)
        quotes = []
        for code, base in [("510300", 4.0), ("159915", 2.0)]:
            close = base + np.cumsum(np.random.randn(n) * 0.02)
            high = close + np.abs(np.random.randn(n) * 0.03)
            low = close - np.abs(np.random.randn(n) * 0.03)
            opn = close + np.random.randn(n) * 0.01
            volume = np.random.randint(100000, 500000, n).astype(float)
            amount = volume * close

            for i in range(n):
                quotes.append({
                    "code": code, "date": str(dates[i])[:10],
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
