"""分钟线数据获取、存储、同步测试"""
import pytest
from engine.data.base import DataSource


class TestMinuteQuotesDataSourceInterface:
    """测试 DataSource 接口是否定义了 fetch_minute_quotes 抽象方法"""

    def test_datasource_has_fetch_minute_quotes(self):
        """DataSource 应该有 fetch_minute_quotes 抽象方法"""
        assert hasattr(DataSource, 'fetch_minute_quotes')
        # 验证方法确实是抽象的，不是普通方法
        assert getattr(DataSource.fetch_minute_quotes, '__isabstractmethod__', False)


from unittest.mock import patch, MagicMock
from engine.data.akshare_source import AkshareSource


class TestAkshareMinuteQuotes:
    """测试 AkshareSource 分钟线获取"""

    @patch('engine.data.akshare_source.ak')
    def test_fetch_etf_minute_quotes(self, mock_ak):
        """测试 ETF 分钟线获取"""
        import pandas as pd
        mock_df = pd.DataFrame({
            '时间': ['2024-01-15 09:31:00', '2024-01-15 09:32:00'],
            '开盘': [4.10, 4.11],
            '收盘': [4.11, 4.12],
            '最高': [4.12, 4.13],
            '最低': [4.09, 4.10],
            '成交量': [100000, 120000],
            '成交额': [410000, 492000],
        })
        mock_ak.fund_etf_hist_min_em.return_value = mock_df

        source = AkshareSource()
        result = source.fetch_minute_quotes('510300', '5')

        assert len(result) == 2
        assert result[0]['datetime'] == '2024-01-15 09:31:00'
        assert result[0]['open'] == 4.10
        assert result[0]['close'] == 4.11
        assert result[0]['high'] == 4.12
        assert result[0]['low'] == 4.09
        assert result[0]['volume'] == 100000
        assert result[0]['amount'] == 410000

    @patch('engine.data.akshare_source.ak')
    def test_fetch_etf_minute_quotes_empty(self, mock_ak):
        """测试 ETF 分钟线获取返回空数据"""
        import pandas as pd
        mock_ak.fund_etf_hist_min_em.return_value = pd.DataFrame()

        source = AkshareSource()
        result = source.fetch_minute_quotes('510300', '5')

        assert result == []

    @patch('engine.data.akshare_source.ak')
    def test_fetch_etf_minute_quotes_exception(self, mock_ak):
        """测试 ETF 分钟线获取异常处理"""
        mock_ak.fund_etf_hist_min_em.side_effect = Exception("API error")

        source = AkshareSource()
        result = source.fetch_minute_quotes('510300', '5')

        assert result == []

    @patch('engine.data.akshare_source.ak')
    def test_fetch_lof_minute_quotes(self, mock_ak):
        """测试 LOF 分钟线获取"""
        import pandas as pd
        mock_df = pd.DataFrame({
            '时间': ['2024-01-15 09:31:00'],
            '开盘': [1.50],
            '收盘': [1.51],
            '最高': [1.52],
            '最低': [1.49],
            '成交量': [50000],
            '成交额': [75000],
        })
        mock_ak.fund_etf_hist_min_em.side_effect = Exception("Not ETF")
        mock_ak.fund_lof_hist_min_em.return_value = mock_df

        source = AkshareSource()
        result = source.fetch_minute_quotes('162411', '5')

        assert len(result) == 1
        assert result[0]['datetime'] == '2024-01-15 09:31:00'


import os
import tempfile
from engine.models.database import Database


class TestMinuteQuoteTable:
    """测试 minute_quote 数据库表"""

    def setup_method(self):
        """每个测试前创建临时数据库"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = Database(self.db_path)
        self.db.init()

    def teardown_method(self):
        """每个测试后清理临时数据库"""
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_minute_quote_table_exists(self):
        """测试 minute_quote 表被创建"""
        tables = self.db.get_tables()
        assert 'minute_quote' in tables

    def test_upsert_minute_quotes(self):
        """测试插入分钟线数据"""
        quotes = [
            {
                "code": "510300",
                "datetime": "2024-01-15 09:31:00",
                "period": "5",
                "open": 4.10,
                "close": 4.11,
                "high": 4.12,
                "low": 4.09,
                "volume": 100000,
                "amount": 410000,
            },
            {
                "code": "510300",
                "datetime": "2024-01-15 09:36:00",
                "period": "5",
                "open": 4.11,
                "close": 4.12,
                "high": 4.13,
                "low": 4.10,
                "volume": 120000,
                "amount": 492000,
            },
        ]
        self.db.upsert_minute_quotes(quotes)

        result = self.db.get_minute_quotes("510300", "5", "2024-01-15 00:00:00", "2024-01-15 23:59:59")
        assert len(result) == 2
        assert result[0]["open"] == 4.10
        assert result[1]["close"] == 4.12

    def test_upsert_minute_quotes_duplicate(self):
        """测试 UPSERT 逻辑（重复插入应更新）"""
        quote = {
            "code": "510300",
            "datetime": "2024-01-15 09:31:00",
            "period": "5",
            "open": 4.10,
            "close": 4.11,
            "high": 4.12,
            "low": 4.09,
            "volume": 100000,
            "amount": 410000,
        }
        self.db.upsert_minute_quotes([quote])

        # 更新同一条记录
        quote["close"] = 4.15
        self.db.upsert_minute_quotes([quote])

        result = self.db.get_minute_quotes("510300", "5", "2024-01-15 00:00:00", "2024-01-15 23:59:59")
        assert len(result) == 1
        assert result[0]["close"] == 4.15

    def test_get_latest_minute_datetime(self):
        """测试获取最新时间戳"""
        quotes = [
            {"code": "510300", "datetime": "2024-01-15 09:31:00", "period": "5",
             "open": 4.10, "close": 4.11, "high": 4.12, "low": 4.09, "volume": 100000, "amount": 410000},
            {"code": "510300", "datetime": "2024-01-15 10:31:00", "period": "5",
             "open": 4.11, "close": 4.12, "high": 4.13, "low": 4.10, "volume": 120000, "amount": 492000},
        ]
        self.db.upsert_minute_quotes(quotes)

        latest = self.db.get_latest_minute_datetime("510300", "5")
        assert latest == "2024-01-15 10:31:00"

    def test_get_latest_minute_datetime_empty(self):
        """测试无数据时返回 None"""
        latest = self.db.get_latest_minute_datetime("510300", "5")
        assert latest is None
