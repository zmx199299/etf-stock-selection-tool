import pytest
from unittest.mock import Mock
from engine.sync import DataSyncPipeline


def test_sync_fund_complete():
    """测试 sync_fund_complete 方法正确抓取完整数据"""
    db = Mock()
    source = Mock()
    pipeline = DataSyncPipeline(db, source)

    # Mock 数据源返回数据
    source.fetch_minute_quotes = Mock(
        side_effect=lambda code, period, start_date=None: []
    )
    source.fetch_daily_quotes = Mock(return_value=[])
    source.fetch_nav = Mock(return_value=[])

    # Mock 数据库方法
    db.upsert_minute_quotes = Mock()
    db.upsert_daily_quotes = Mock()
    db._update_nav = Mock()

    # 调用
    result = pipeline.sync_fund_complete("510300")

    # 验证 fetch_minute_quotes 被调用了3次（1m, 5m, 60m）
    assert source.fetch_minute_quotes.call_count == 3

    # 验证 1分线传入了 start_date（最近5天）
    call_1m = source.fetch_minute_quotes.call_args_list[0]
    assert call_1m[0][1] == "1"  # period
    assert call_1m[1]["start_date"] is not None  # 应该有 start_date

    # 验证 fetch_daily_quotes 被调用（无日期限制）
    source.fetch_daily_quotes.assert_called_once_with("510300")

    # 验证返回结果
    assert "minute_counts" in result
    assert "daily_count" in result
    assert "nav_count" in result
