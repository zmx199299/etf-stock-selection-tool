import pandas as pd
import numpy as np
import pytest
from engine.scoring.patterns import PatternRecognizer

@pytest.fixture
def v_reversal_data():
    # 模拟一个典型的单日V型反转：开盘平稳，盘中大幅下跌，收盘大幅拉升接近最高点
    df = pd.DataFrame({
        "open": [10.0, 9.8, 9.5],
        "high": [10.2, 9.9, 9.6],
        "low": [9.8, 9.5, 8.5], # 盘中深跌
        "close": [9.9, 9.6, 9.5], # 收盘拉回
        "volume": [1000, 1200, 3000] # 底部放量
    })
    return df

@pytest.fixture
def normal_data():
    # 模拟普通波动，没有V型反转
    df = pd.DataFrame({
        "open": [10.0, 10.1, 10.2],
        "high": [10.2, 10.3, 10.4],
        "low": [9.8, 10.0, 10.1],
        "close": [10.1, 10.2, 10.3],
        "volume": [1000, 1100, 1050]
    })
    return df

def test_detect_v_reversal(v_reversal_data):
    recognizer = PatternRecognizer()
    result = recognizer.detect_v_reversal(v_reversal_data)
    # 断言识别到了V型反转
    assert result is True

def test_no_v_reversal(normal_data):
    recognizer = PatternRecognizer()
    result = recognizer.detect_v_reversal(normal_data)
    # 断言未识别到V型反转
    assert result is False

def test_detect_all_patterns(v_reversal_data):
    recognizer = PatternRecognizer()
    results = recognizer.detect_all(v_reversal_data)
    assert "v_reversal" in results
    assert results["v_reversal"] is True
