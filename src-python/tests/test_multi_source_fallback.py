# src-python/tests/test_multi_source_fallback.py
"""多源容错爬取的单元测试：验证 AkshareSource 在主源失败时自动切换备用源"""

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock


class TestFetchFundListMultiSource:
    """fetch_fund_list 应并发尝试 _em 和 _sina 两套接口，取数量多的"""

    @patch("engine.data.akshare_source.ak")
    def test_em_fails_falls_back_to_sina(self, mock_ak):
        """东方财富接口全挂时，应 fallback 到新浪接口"""
        from engine.data.akshare_source import AkshareSource

        # _em 接口抛 ConnectionError
        mock_ak.fund_etf_spot_em.side_effect = ConnectionError("Remote end closed")
        mock_ak.fund_lof_spot_em.side_effect = ConnectionError("Remote end closed")

        # _sina 接口正常返回
        mock_ak.fund_etf_category_sina.return_value = pd.DataFrame(
            [
                {"代码": "510300", "名称": "沪深300ETF", "最新价": 4.1, "成交量": 1000},
                {"代码": "159915", "名称": "创业板ETF", "最新价": 2.5, "成交量": 500},
            ]
        )
        # fund_name_em 提供基金类型元数据
        mock_ak.fund_name_em.return_value = pd.DataFrame(
            [
                {
                    "基金代码": "510300",
                    "基金简称": "沪深300ETF",
                    "基金类型": "指数型-股票",
                },
                {
                    "基金代码": "159915",
                    "基金简称": "创业板ETF",
                    "基金类型": "指数型-股票",
                },
            ]
        )

        source = AkshareSource()
        funds = source.fetch_fund_list()

        assert len(funds) >= 2
        codes = [f["code"] for f in funds]
        assert "510300" in codes
        assert "159915" in codes

    @patch("engine.data.akshare_source.ak")
    def test_both_sources_work_picks_larger(self, mock_ak):
        """两个源都成功时，取数量更多的那个"""
        from engine.data.akshare_source import AkshareSource

        # _em 返回 1 只
        mock_ak.fund_etf_spot_em.return_value = pd.DataFrame(
            [
                {"代码": "510300", "名称": "沪深300ETF"},
            ]
        )
        mock_ak.fund_lof_spot_em.return_value = pd.DataFrame()

        # _sina 返回 3 只（更多）
        mock_ak.fund_etf_category_sina.return_value = pd.DataFrame(
            [
                {"代码": "510300", "名称": "沪深300ETF", "最新价": 4.1, "成交量": 1000},
                {"代码": "159915", "名称": "创业板ETF", "最新价": 2.5, "成交量": 500},
                {"代码": "510500", "名称": "中证500ETF", "最新价": 6.0, "成交量": 800},
            ]
        )
        mock_ak.fund_name_em.return_value = pd.DataFrame(
            [
                {
                    "基金代码": "510300",
                    "基金简称": "沪深300ETF",
                    "基金类型": "指数型-股票",
                },
                {
                    "基金代码": "159915",
                    "基金简称": "创业板ETF",
                    "基金类型": "指数型-股票",
                },
                {
                    "基金代码": "510500",
                    "基金简称": "中证500ETF",
                    "基金类型": "指数型-股票",
                },
            ]
        )

        source = AkshareSource()
        funds = source.fetch_fund_list()

        # 应该选新浪那个更大的结果
        assert len(funds) >= 3

    @patch("engine.data.akshare_source.ak")
    def test_both_sources_fail_returns_empty(self, mock_ak):
        """两个源都失败时，返回空列表（不崩溃）"""
        from engine.data.akshare_source import AkshareSource

        mock_ak.fund_etf_spot_em.side_effect = ConnectionError("fail")
        mock_ak.fund_lof_spot_em.side_effect = ConnectionError("fail")
        mock_ak.fund_etf_category_sina.side_effect = ConnectionError("fail")
        mock_ak.fund_name_em.side_effect = ConnectionError("fail")

        source = AkshareSource()
        funds = source.fetch_fund_list()

        assert funds == []

    @patch("engine.data.akshare_source.ak")
    def test_sina_excludes_money_and_bond_funds(self, mock_ak):
        """新浪源也应排除货币/债券基金"""
        from engine.data.akshare_source import AkshareSource

        mock_ak.fund_etf_spot_em.side_effect = ConnectionError("fail")
        mock_ak.fund_lof_spot_em.side_effect = ConnectionError("fail")

        mock_ak.fund_etf_category_sina.return_value = pd.DataFrame(
            [
                {"代码": "510300", "名称": "沪深300ETF", "最新价": 4.1, "成交量": 1000},
                {
                    "代码": "511880",
                    "名称": "银华日利货币ETF",
                    "最新价": 100,
                    "成交量": 100,
                },
            ]
        )
        mock_ak.fund_name_em.return_value = pd.DataFrame(
            [
                {
                    "基金代码": "510300",
                    "基金简称": "沪深300ETF",
                    "基金类型": "指数型-股票",
                },
                {
                    "基金代码": "511880",
                    "基金简称": "银华日利货币ETF",
                    "基金类型": "货币型",
                },
            ]
        )

        source = AkshareSource()
        funds = source.fetch_fund_list()

        codes = [f["code"] for f in funds]
        assert "510300" in codes
        # 货币基金应该被排除或标记
        money_funds = [f for f in funds if f["code"] == "511880"]
        if money_funds:
            assert money_funds[0]["is_excluded"] == 1


class TestFetchDailyQuotesMultiSource:
    """fetch_daily_quotes 应先试 _em，失败后 fallback 到 _sina"""

    @patch("engine.data.akshare_source.ak")
    def test_em_fails_falls_back_to_sina(self, mock_ak):
        """东方财富日线失败时，应 fallback 到新浪日线"""
        from engine.data.akshare_source import AkshareSource

        # _em 接口挂了
        mock_ak.fund_etf_hist_em.side_effect = ConnectionError("Remote end closed")

        # _sina 接口正常
        mock_ak.fund_etf_hist_sina.return_value = pd.DataFrame(
            [
                {
                    "date": "2026-04-01",
                    "open": 4.0,
                    "close": 4.1,
                    "high": 4.2,
                    "low": 3.9,
                    "volume": 10000,
                    "amount": 41000,
                },
                {
                    "date": "2026-04-02",
                    "open": 4.1,
                    "close": 4.15,
                    "high": 4.2,
                    "low": 4.0,
                    "volume": 12000,
                    "amount": 49800,
                },
            ]
        )

        source = AkshareSource()
        quotes = source.fetch_daily_quotes("510300", start_date="2026-04-01")

        assert len(quotes) >= 1
        first = quotes[0]
        assert "date" in first
        assert "open" in first
        assert "close" in first

    @patch("engine.data.akshare_source.ak")
    def test_em_works_does_not_call_sina(self, mock_ak):
        """东方财富日线正常时，不应调用新浪接口"""
        from engine.data.akshare_source import AkshareSource

        mock_ak.fund_etf_hist_em.return_value = pd.DataFrame(
            [
                {
                    "日期": "2026-04-01",
                    "开盘": 4.0,
                    "收盘": 4.1,
                    "最高": 4.2,
                    "最低": 3.9,
                    "成交量": 10000,
                    "成交额": 41000,
                },
            ]
        )

        source = AkshareSource()
        quotes = source.fetch_daily_quotes("510300")

        assert len(quotes) == 1
        mock_ak.fund_etf_hist_sina.assert_not_called()

    @patch("engine.data.akshare_source.ak")
    def test_both_fail_returns_empty(self, mock_ak):
        """两个源都失败时，返回空列表"""
        from engine.data.akshare_source import AkshareSource

        mock_ak.fund_etf_hist_em.side_effect = ConnectionError("fail")
        mock_ak.fund_etf_hist_sina.side_effect = ConnectionError("fail")

        source = AkshareSource()
        quotes = source.fetch_daily_quotes("510300")

        assert quotes == []

    @patch("engine.data.akshare_source.ak")
    def test_sina_fallback_converts_format(self, mock_ak):
        """新浪 fallback 应将数据转换为统一格式"""
        from engine.data.akshare_source import AkshareSource

        mock_ak.fund_etf_hist_em.side_effect = ConnectionError("fail")
        mock_ak.fund_etf_hist_sina.return_value = pd.DataFrame(
            [
                {
                    "date": "2026-04-01",
                    "open": 4.0,
                    "close": 4.1,
                    "high": 4.2,
                    "low": 3.9,
                    "volume": 10000,
                    "amount": 41000,
                },
            ]
        )

        source = AkshareSource()
        quotes = source.fetch_daily_quotes("510300", start_date="2026-04-01")

        assert len(quotes) == 1
        q = quotes[0]
        # 验证统一格式的所有必要字段
        for key in ["date", "open", "close", "high", "low", "volume", "amount"]:
            assert key in q, f"缺少字段: {key}"
        assert isinstance(q["open"], float)
        assert isinstance(q["close"], float)


class TestEmSourceSkipAfterConsecutiveFailures:
    """em 数据源连续失败后应跳过 em，直接使用 sina"""

    @patch("engine.data.akshare_source.ak")
    def test_skips_em_after_consecutive_failures(self, mock_ak):
        """em 连续失败 N 次后，后续调用应直接跳过 em"""
        from engine.data.akshare_source import AkshareSource

        source = AkshareSource()

        # em 始终失败
        mock_ak.fund_etf_hist_em.side_effect = ConnectionError("Remote end closed")
        # sina 始终成功
        mock_ak.fund_etf_hist_sina.return_value = pd.DataFrame(
            [
                {
                    "date": "2026-04-01",
                    "open": 4.0,
                    "close": 4.1,
                    "high": 4.2,
                    "low": 3.9,
                    "volume": 10000,
                    "amount": 41000,
                },
            ]
        )

        # 先让 em 失败足够多次触发跳过阈值（默认 5 次）
        for i in range(5):
            source.fetch_daily_quotes(f"51030{i}", start_date="2026-04-01")

        # 重置 mock 调用计数
        mock_ak.fund_etf_hist_em.reset_mock()
        mock_ak.fund_etf_hist_sina.reset_mock()

        # 第 6 次调用：em 应该被跳过，不再调用
        source.fetch_daily_quotes("510300", start_date="2026-04-01")

        mock_ak.fund_etf_hist_em.assert_not_called()
        mock_ak.fund_etf_hist_sina.assert_called_once()

    @patch("engine.data.akshare_source.ak")
    def test_em_success_resets_failure_counter(self, mock_ak):
        """em 成功一次后应重置失败计数器"""
        from engine.data.akshare_source import AkshareSource

        source = AkshareSource()

        # em 先失败 3 次
        mock_ak.fund_etf_hist_em.side_effect = ConnectionError("fail")
        mock_ak.fund_etf_hist_sina.return_value = pd.DataFrame(
            [
                {
                    "date": "2026-04-01",
                    "open": 4.0,
                    "close": 4.1,
                    "high": 4.2,
                    "low": 3.9,
                    "volume": 10000,
                    "amount": 41000,
                },
            ]
        )
        for i in range(3):
            source.fetch_daily_quotes(f"51030{i}", start_date="2026-04-01")

        # em 恢复正常
        mock_ak.fund_etf_hist_em.side_effect = None
        mock_ak.fund_etf_hist_em.return_value = pd.DataFrame(
            [
                {
                    "日期": "2026-04-01",
                    "开盘": 4.0,
                    "收盘": 4.1,
                    "最高": 4.2,
                    "最低": 3.9,
                    "成交量": 10000,
                    "成交额": 41000,
                },
            ]
        )
        source.fetch_daily_quotes("510300", start_date="2026-04-01")

        # em 失败计数应已重置，现在应该是 0
        assert source._em_consecutive_failures == 0

    @patch("engine.data.akshare_source.ak")
    def test_em_skip_threshold_configurable(self, mock_ak):
        """em 跳过阈值应可配置"""
        from engine.data.akshare_source import AkshareSource

        source = AkshareSource(em_skip_threshold=3)

        mock_ak.fund_etf_hist_em.side_effect = ConnectionError("fail")
        mock_ak.fund_etf_hist_sina.return_value = pd.DataFrame(
            [
                {
                    "date": "2026-04-01",
                    "open": 4.0,
                    "close": 4.1,
                    "high": 4.2,
                    "low": 3.9,
                    "volume": 10000,
                    "amount": 41000,
                },
            ]
        )

        # 失败 3 次达到阈值
        for i in range(3):
            source.fetch_daily_quotes(f"51030{i}", start_date="2026-04-01")

        mock_ak.fund_etf_hist_em.reset_mock()

        # 第 4 次应跳过 em
        source.fetch_daily_quotes("510300", start_date="2026-04-01")
        mock_ak.fund_etf_hist_em.assert_not_called()
