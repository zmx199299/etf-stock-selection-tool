"""分析数据服务测试：将数据库数据转换为前端 AnalysisPeriod 格式"""
import os
import tempfile
import pytest
from engine.models.database import Database
from engine.scoring.indicators import TechnicalIndicators
from engine.services.analysis_service import AnalysisService


class TestAnalysisService:
    """测试分析数据服务"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init()
        self.indicators = TechnicalIndicators()
        self.service = AnalysisService(self.db, self.indicators)

        # 插入测试基金
        self.db.upsert_fund_info([{
            "code": "510300",
            "name": "沪深300ETF",
            "fund_type": "ETF",
            "invest_type": "指数型",
            "t_plus": "T+1",
            "list_date": "2020-01-01",
            "is_excluded": 0,
            "has_market_data": 1,
        }])

    def teardown_method(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def _insert_test_daily_quotes(self):
        """插入测试日线数据"""
        quotes = []
        base_price = 4.00
        for i in range(30):
            date = f"2024-01-{i+1:02d}"
            open_p = base_price + i * 0.02
            close_p = base_price + i * 0.02 + 0.01
            quotes.append({
                "code": "510300",
                "date": date,
                "open": open_p,
                "close": close_p,
                "high": close_p + 0.02,
                "low": open_p - 0.02,
                "volume": 1000000 + i * 10000,
                "amount": (open_p + close_p) * 500000,
                "nav": None,
                "premium_rate": None,
                "prev_close": None,
                "is_suspended": 0,
                "suspended_days": 0,
            })
        self.db.upsert_daily_quotes(quotes)

    def _insert_test_minute_quotes(self):
        """插入测试分钟线数据"""
        quotes = []
        base_price = 4.10
        for i in range(20):
            hour = 9 + (i * 5 + 31) // 60
            minute = (i * 5 + 31) % 60
            if hour >= 11 and minute >= 30:
                hour = 13
                minute = (i * 5 + 31 - 120) % 60
            datetime_str = f"2024-01-15 {hour:02d}:{minute:02d}:00"
            quotes.append({
                "code": "510300",
                "datetime": datetime_str,
                "period": "5",
                "open": base_price + i * 0.01,
                "close": base_price + i * 0.01 + 0.005,
                "high": base_price + i * 0.01 + 0.015,
                "low": base_price + i * 0.01 - 0.005,
                "volume": 50000 + i * 1000,
                "amount": (base_price + i * 0.01) * 50000,
            })
        self.db.upsert_minute_quotes(quotes)

    def test_get_day_period(self):
        """测试获取日线周期数据"""
        self._insert_test_daily_quotes()
        period = self.service.get_day_period("510300")

        assert period["key"] == "day"
        assert period["label"] == "日K"
        assert len(period["candles"]) > 0
        assert len(period["volumes"]) > 0
        assert len(period["timeAxis"]) > 0
        assert len(period["priceAxis"]) > 0
        # 检查 candles 格式 [open, high, low, close]
        candle = period["candles"][0]
        assert len(candle) == 4

    def test_get_minute_period(self):
        """测试获取分钟线周期数据"""
        self._insert_test_minute_quotes()
        period = self.service.get_minute_period("510300", "m5", "5")

        assert period["key"] == "m5"
        assert period["label"] == "5分"
        assert len(period["candles"]) > 0
        assert len(period["volumes"]) > 0

    def test_get_intraday_period(self):
        """测试获取分时数据"""
        # 插入当日 1 分钟线数据（分时图需要 period="1" 和当天日期）
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        quotes = []
        base_price = 4.10
        for i in range(20):
            hour = 9 + (i * 5 + 31) // 60
            minute = (i * 5 + 31) % 60
            if hour >= 11 and minute >= 30:
                hour = 13
                minute = (i * 5 + 31 - 120) % 60
            datetime_str = f"{today} {hour:02d}:{minute:02d}:00"
            quotes.append({
                "code": "510300",
                "datetime": datetime_str,
                "period": "1",
                "open": base_price + i * 0.01,
                "close": base_price + i * 0.01 + 0.005,
                "high": base_price + i * 0.01 + 0.015,
                "low": base_price + i * 0.01 - 0.005,
                "volume": 50000 + i * 1000,
                "amount": (base_price + i * 0.01) * 50000,
            })
        self.db.upsert_minute_quotes(quotes)

        period = self.service.get_intraday_period("510300")

        assert period["key"] == "intraday"
        assert period["label"] == "分时"
        assert len(period["linePoints"]) > 0
        assert len(period["avgLinePoints"]) > 0
        assert period["candles"] == []  # 分时图不使用 candles

    def test_get_analysis_data(self):
        """测试获取完整分析数据"""
        self._insert_test_daily_quotes()
        self._insert_test_minute_quotes()

        result = self.service.get_analysis_data("510300")

        assert result["code"] == "510300"
        assert result["name"] == "沪深300ETF"
        assert "periods" in result
        assert "day" in result["periods"]
        assert "m5" in result["periods"]

    def test_get_analysis_data_not_found(self):
        """测试基金不存在时返回 None"""
        result = self.service.get_analysis_data("999999")
        assert result is None

    def test_metrics_generation(self):
        """测试技术指标生成"""
        self._insert_test_daily_quotes()
        period = self.service.get_day_period("510300")

        assert "metrics" in period
        assert len(period["metrics"]) > 0
        # 检查指标格式
        metric = period["metrics"][0]
        assert "label" in metric
        assert "value" in metric
        assert "summary" in metric
        assert "tone" in metric
        assert metric["tone"] in ("bullish", "neutral", "bearish")
