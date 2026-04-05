import os
import json
import pytest
import pandas as pd
from engine.models.database import Database
from engine.data.base import DataSource
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer
from engine.scoring.patterns import PatternRecognizer
from engine.scoring.calculator import CostCalculator
from engine.utils.config import ConfigManager

class MockDataSource(DataSource):
    """用于测试的模拟数据源，不需要真实请求网络"""
    def fetch_fund_list(self):
        return [{"code": "510300", "name": "Mock Fund 510300", "fund_type": "ETF", "invest_type": "Stock", "t_plus": 1, "list_date": "2012-05-04", "is_excluded": False}]
        
    def fetch_daily_quotes(self, code: str, start_date: str = None):
        # 模拟生成几十天的连续数据，制造一个近期的"V型反转"
        n = 30
        dates = pd.date_range(end="2023-10-01", periods=n)
        
        # 基础平稳数据
        opn = [10.0] * (n - 1)
        close = [10.1] * (n - 1)
        high = [10.2] * (n - 1)
        low = [9.9] * (n - 1)
        volume = [1000] * (n - 1)
        amount = [10000] * (n - 1)
        
        # 最后一天制造V型反转
        opn.append(10.1)
        close.append(10.2)
        high.append(10.3)
        low.append(9.0) # 深跌下影线
        volume.append(5000)
        amount.append(50000)
        
        df = pd.DataFrame({
            "date": dates,
            "open": opn, "close": close, "high": high, "low": low,
            "volume": volume, "amount": amount
        })
        # 转成 dict 列表返回，以匹配 DataSource 的抽象接口要求
        return df.to_dict('records')

    def fetch_nav(self, code: str, start_date: str = None):
        return [{"date": "2023-10-01", "nav": 10.2}]

    def fetch_minute_quotes(self, code: str, period: str):
        return []


@pytest.fixture
def mock_env(tmp_path):
    # Setup test DB and config
    db_path = str(tmp_path / "test_integration.db")
    config_path = str(tmp_path / "config.json")
    
    # 建立测试配置
    config_data = {
        "trading": {"budget": 100000.0, "commission_rate": 0.0001, "min_commission": 0.0, "stamp_duty": 0.0},
        "analysis": {"score_threshold": 50}
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f)
        
    db = Database(db_path)
    
    yield {
        "db": db,
        "config_path": config_path
    }
    
    # Teardown (optional since using tmp_path, but good practice)
    db.close()

def test_stage_1_workflow(mock_env):
    """
    测试阶段一工作流:
    1. 同步日线数据
    2. 计算技术指标
    3. 计算得分
    4. 识别V型反转
    5. 根据预算计算预估佣金并产生推荐
    """
    symbol = "510300"
    
    # 1. 模拟数据获取并存入DB
    source = MockDataSource()
    quotes = source.fetch_daily_quotes(symbol)
    df = pd.DataFrame(quotes)
    
    db = mock_env["db"]
    # (假设通过某种方式将 df 存入 DB，这里直接使用 df 模拟从 DB 读出后进行计算)
    
    # 2. 计算技术指标
    ti = TechnicalIndicators()
    df_with_ti = ti.compute_all(df)
    assert not df_with_ti.empty
    
    # 3. 计算得分
    scorer = Scorer()
    score_result = scorer.score(df_with_ti)
    assert "total_score" in score_result
    
    # 4. 识别形态
    pattern = PatternRecognizer()
    pattern_result = pattern.detect_all(df_with_ti)
    # 因为我们在 mock 数据中最后一天故意制造了V型反转
    assert pattern_result.get("v_reversal") is True
    
    # 5. 读取配置并进行业务预算/成本计算
    config_mgr = ConfigManager(mock_env["config_path"])
    config = config_mgr.load()
    
    # 将旧的简单格式转换为新的费率结构
    fees_config = {
        "etf": {
            "commission_rate": config["trading"].get("commission_rate", 0.0001),
            "min_commission": config["trading"].get("min_commission", 0.0),
            "stamp_duty": config["trading"].get("stamp_duty", 0.0)
        }
    }
    
    calculator = CostCalculator(fees_config)
    
    # 假设推荐全仓买入
    budget = config["trading"]["budget"]
    buy_cost = calculator.calculate_buy_cost(budget, "etf")
    assert buy_cost == 10.0 # 100000 * 0.0001 = 10，免5最低收实际佣金
    
    # 整合输出
    final_output = {
        "symbol": symbol,
        "score": score_result,
        "patterns": pattern_result,
        "budget_advice": {
            "amount": budget,
            "estimated_fee": buy_cost
        }
    }
    
    assert final_output["patterns"]["v_reversal"] is True
    assert final_output["budget_advice"]["estimated_fee"] == 10.0
