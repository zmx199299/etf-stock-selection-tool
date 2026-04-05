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
