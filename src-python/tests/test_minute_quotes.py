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
