import pytest
from engine.scoring.calculator import CostCalculator

def test_etf_buy_cost_normal():
    # 测试普通ETF（无免5）
    fees_config = {
        "etf": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
        "lof": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
        "stock": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.001}
    }
    calculator = CostCalculator(fees_config)
    cost = calculator.calculate_buy_cost(10000.0, "etf")
    assert cost == 5.0
    cost2 = calculator.calculate_buy_cost(100000.0, "etf")
    assert cost2 == 10.0

def test_etf_buy_cost_free_5():
    # 测试免5的ETF
    fees_config = {
        "etf": {"commission_rate": 0.0001, "min_commission": 0.0, "stamp_duty": 0.0},
        "lof": {"commission_rate": 0.0001, "min_commission": 0.0, "stamp_duty": 0.0},
        "stock": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.001}
    }
    calculator = CostCalculator(fees_config)
    cost = calculator.calculate_buy_cost(10000.0, "etf")
    assert cost == 1.0

def test_sell_cost_stock_with_stamp_duty():
    # 测试卖出股票时带印花税
    fees_config = {
        "etf": {"commission_rate": 0.0001, "min_commission": 0.0, "stamp_duty": 0.0},
        "lof": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
        "stock": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.001}
    }
    calculator = CostCalculator(fees_config)
    # 卖出金额 10000，佣金5元，印花税 10000 * 0.001 = 10，总成本 15
    cost = calculator.calculate_sell_cost(10000.0, "stock")
    assert cost == 15.0

def test_profit_calculation():
    # 测试净利润计算
    fees_config = {
        "etf": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
        "lof": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
        "stock": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.001}
    }
    calculator = CostCalculator(fees_config)
    # ETF: 买入 10000，佣金 5, 卖出 11000，佣金 5
    # 毛利 1000，净利 1000 - 10 = 990
    profit = calculator.calculate_net_profit(10000.0, 11000.0, "etf")
    assert profit == 990.0

    # Stock: 买入 10000，佣金 5, 卖出 11000，佣金 5, 印花税 11
    # 毛利 1000，净利 1000 - 5 - 5 - 11 = 979
    profit_stock = calculator.calculate_net_profit(10000.0, 11000.0, "stock")
    assert profit_stock == 979.0
