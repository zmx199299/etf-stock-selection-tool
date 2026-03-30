# src-python/tests/test_scorer.py
import pandas as pd
import numpy as np
import pytest
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer

@pytest.fixture
def sample_indicators():
    np.random.seed(42)
    n = 60
    close = 10 + np.cumsum(np.random.randn(n) * 0.1)
    high = close + np.abs(np.random.randn(n) * 0.05)
    low = close - np.abs(np.random.randn(n) * 0.05)
    opn = close + np.random.randn(n) * 0.02
    volume = np.random.randint(10000, 100000, n).astype(float)
    df = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n),
        "open": opn, "close": close, "high": high, "low": low,
        "volume": volume, "amount": volume * close,
    })
    ti = TechnicalIndicators()
    return ti.compute_all(df)

def test_score_returns_dict(sample_indicators):
    scorer = Scorer()
    result = scorer.score(sample_indicators)
    assert "total_score" in result
    assert "trend_score" in result
    assert "momentum_score" in result
    assert "volatility_score" in result
    assert "volume_score" in result
    assert "signal" in result

def test_score_range(sample_indicators):
    scorer = Scorer()
    result = scorer.score(sample_indicators)
    assert 0 <= result["total_score"] <= 100
    assert 0 <= result["trend_score"] <= 100
    assert result["signal"] in ["强烈看多","看多","中性","看空","强烈看空"]

def test_custom_weights(sample_indicators):
    weights = {"trend": 0.5, "momentum": 0.2, "volatility": 0.1, "volume": 0.2}
    scorer = Scorer(weights=weights)
    result = scorer.score(sample_indicators)
    assert 0 <= result["total_score"] <= 100

def test_buy_value_score(sample_indicators):
    scorer = Scorer()
    last = sample_indicators.iloc[-1]
    result = scorer.buy_value_score(
        tech_score=65, premium_rate=-0.02,
        reversal_strength=0.7, consecutive_days=3,
        volume_ratio=1.5
    )
    assert 0 <= result <= 100
