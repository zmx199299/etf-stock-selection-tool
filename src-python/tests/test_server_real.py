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
