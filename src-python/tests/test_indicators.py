# src-python/tests/test_indicators.py
import pandas as pd
import numpy as np
import pytest
from engine.scoring.indicators import TechnicalIndicators

@pytest.fixture
def sample_df():
    """构造60天的模拟行情数据"""
    np.random.seed(42)
    n = 60
    close = 10 + np.cumsum(np.random.randn(n) * 0.1)
    high = close + np.abs(np.random.randn(n) * 0.05)
    low = close - np.abs(np.random.randn(n) * 0.05)
    opn = close + np.random.randn(n) * 0.02
    volume = np.random.randint(10000, 100000, n).astype(float)
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n),
        "open": opn, "close": close, "high": high, "low": low,
        "volume": volume, "amount": volume * close,
    })

def test_compute_all_returns_dataframe(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(sample_df)

def test_trend_indicators_exist(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    for col in ["ma5","ma10","ma20","ma60","ema12","ema26","macd","macd_signal","macd_hist"]:
        assert col in result.columns, f"Missing {col}"

def test_momentum_indicators_exist(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    for col in ["rsi6","rsi12","rsi24","k","d","j","wr"]:
        assert col in result.columns, f"Missing {col}"

def test_volatility_indicators_exist(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    for col in ["boll_upper","boll_mid","boll_lower","atr14"]:
        assert col in result.columns, f"Missing {col}"

def test_volume_indicators_exist(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    for col in ["obv","volume_ratio"]:
        assert col in result.columns, f"Missing {col}"
