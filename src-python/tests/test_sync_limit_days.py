import pytest
from unittest.mock import Mock
from engine.sync import DataSyncPipeline


def test_sync_all_with_limit_days():
    """测试 limit_days 参数是否正确传递"""
    db = Mock()
    source = Mock()
    pipeline = DataSyncPipeline(db, source)

    pipeline.sync_fund_list = Mock(return_value=10)
    pipeline.sync_daily_quotes_for_all = Mock(return_value=1000)
    pipeline.sync_nav_for_all = Mock(return_value=50)

    result = pipeline.sync_all(limit_days=60)

    pipeline.sync_daily_quotes_for_all.assert_called_once_with(limit_days=60)
    assert result == {"funds_synced": 10, "quotes_synced": 1000, "nav_updated": 50}
