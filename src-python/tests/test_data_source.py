# src-python/tests/test_data_source.py
import pytest
from engine.data.base import DataSource
from engine.data.akshare_source import AkshareSource

def test_akshare_source_implements_interface():
    source = AkshareSource()
    assert isinstance(source, DataSource)

def test_fetch_fund_list():
    """集成测试：需要联网"""
    source = AkshareSource()
    funds = source.fetch_fund_list()
    if not funds:
        pytest.skip("akshare 基金列表当前返回空结果，外部数据源不可用")
    first = funds[0]
    assert "code" in first
    assert "name" in first
    assert "fund_type" in first

def test_fetch_daily_quotes():
    """集成测试：需要联网，取沪深300ETF近5日数据"""
    source = AkshareSource()
    quotes = source.fetch_daily_quotes("510300", start_date="2026-03-20")
    if not quotes:
        pytest.skip("akshare 日线行情当前返回空结果，外部数据源不可用")
    first = quotes[0]
    for key in ["date","open","close","high","low","volume","amount"]:
        assert key in first

def test_fetch_nav():
    """集成测试：需要联网"""
    source = AkshareSource()
    nav_data = source.fetch_nav("510300", start_date="2026-03-20")
    assert len(nav_data) > 0
    first = nav_data[0]
    assert "date" in first
    assert "nav" in first
