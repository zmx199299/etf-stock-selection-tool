class CostCalculator:
    def __init__(self, fees_config=None):
        """
        fees_config: dict
        {
            "etf": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
            "lof": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
            "stock": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.001}
        }
        """
        if fees_config is None:
            self.fees = {
                "etf": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
                "lof": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.0},
                "stock": {"commission_rate": 0.0001, "min_commission": 5.0, "stamp_duty": 0.001}
            }
        else:
            self.fees = fees_config

    def _get_params(self, asset_type: str):
        asset_type = asset_type.lower()
        if asset_type not in self.fees:
            asset_type = "etf"
        config = self.fees[asset_type]
        return config.get("commission_rate", 0.0), config.get("min_commission", 0.0), config.get("stamp_duty", 0.0)

    def calculate_buy_cost(self, amount: float, asset_type: str = "etf") -> float:
        """计算买入成本（不含印花税）"""
        comm_rate, min_comm, _ = self._get_params(asset_type)
        commission = amount * comm_rate
        if min_comm > 0:
            commission = max(commission, min_comm)
        return commission

    def calculate_sell_cost(self, amount: float, asset_type: str = "etf") -> float:
        """计算卖出成本（包含印花税）"""
        comm_rate, min_comm, stamp_duty = self._get_params(asset_type)
        commission = amount * comm_rate
        if min_comm > 0:
            commission = max(commission, min_comm)
            
        stamp_tax = amount * stamp_duty
        return commission + stamp_tax

    def calculate_net_profit(self, buy_amount: float, sell_amount: float, asset_type: str = "etf") -> float:
        """计算净利润：毛利润减去买入、卖出总成本"""
        gross_profit = sell_amount - buy_amount
        buy_cost = self.calculate_buy_cost(buy_amount, asset_type)
        sell_cost = self.calculate_sell_cost(sell_amount, asset_type)
        
        return gross_profit - buy_cost - sell_cost
