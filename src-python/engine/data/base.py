# src-python/engine/data/base.py
from abc import ABC, abstractmethod

class DataSource(ABC):
    """数据源抽象接口，新数据源只需实现此接口即可接入"""

    @abstractmethod
    def fetch_fund_list(self) -> list[dict]:
        """获取所有场内基金列表
        返回: [{"code","name","fund_type","invest_type","t_plus","list_date","is_excluded"}]
        """
        ...

    @abstractmethod
    def fetch_daily_quotes(self, code: str, start_date: str = None) -> list[dict]:
        """获取指定基金的日线行情
        返回: [{"date","open","close","high","low","volume","amount"}]
        """
        ...

    @abstractmethod
    def fetch_nav(self, code: str, start_date: str = None) -> list[dict]:
        """获取指定基金的净值数据
        返回: [{"date","nav"}]
        """
        ...

    @abstractmethod
    def fetch_minute_quotes(self, code: str, period: str) -> list[dict]:
        """获取指定基金的分钟线行情
        Args:
            code: 基金代码
            period: 周期标识 '1', '5', '60'
        Returns:
            [{"datetime": "YYYY-MM-DD HH:MM:SS", "open": float, "close": float,
              "high": float, "low": float, "volume": float, "amount": float}]
        """
        ...
