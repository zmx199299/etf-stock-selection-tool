"""
共享测试 fixtures。
所有外部依赖均使用 mock，禁止依赖真实网络。
"""

import pandas as pd
import pytest


@pytest.fixture
def sample_fund_dict() -> dict[str, str]:
    """少量示例基金字典。"""
    return {
        "510050": "华夏上证50ETF",
        "510300": "华泰柏瑞沪深300ETF",
        "161725": "招商中证白酒指数LOF",
        "513050": "易方达中概互联网50ETF",  # 跨境，T+0
        "518880": "国泰黄金ETF",  # 黄金，T+0
    }


def _make_hist_df(
    dates: list[str],
    open_: float = 3.0,
    close: float = 3.0,
    high: float = 3.14,
    low: float = 2.86,
    volume: int = 1_000_000,
) -> pd.DataFrame:
    """构造标准历史行情 DataFrame。"""
    n = len(dates)
    return pd.DataFrame(
        {
            "date": dates,
            "开盘": [open_] * n,
            "收盘": [close] * n,
            "最高": [high] * n,
            "最低": [low] * n,
            "成交量": [volume] * n,
        }
    )


@pytest.fixture
def trade_dates() -> list[str]:
    """5个连续交易日（用于测试）。"""
    return [
        "2026-03-20",
        "2026-03-23",
        "2026-03-24",
        "2026-03-25",
        "2026-03-26",
        "2026-03-27",
    ]


@pytest.fixture
def hist_df_v_shape(trade_dates: list[str]) -> pd.DataFrame:
    """
    满足V型反转条件的历史行情：
      昨收=3.0, 最高=3.105, 最低=2.97
      振幅=(3.105-2.97)/3.0*100=4.5%，low_drop=(2.97-3.0)/3.0*100=-1.0%
    """
    # 构造满足3天条件的序列（共需4行，index 0 为参考昨收）
    dates = trade_dates[:6]  # 6行数据
    rows = []
    base_close = 3.0
    for i, d in enumerate(dates):
        if i == 0:
            rows.append(
                {
                    "date": d,
                    "开盘": 3.0,
                    "收盘": base_close,
                    "最高": 3.0,
                    "最低": 3.0,
                    "成交量": 1_000_000,
                }
            )
        else:
            # 昨收=3.0, 最高=3.105, 最低=2.97 → 振幅4.5%，下跌1.0%
            rows.append(
                {
                    "date": d,
                    "开盘": 3.0,
                    "收盘": 3.0,
                    "最高": 3.105,
                    "最低": 2.97,
                    "成交量": 1_500_000,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def mock_trade_calendar(monkeypatch: pytest.MonkeyPatch) -> None:
    """mock akshare 交易日历。"""
    import akshare as ak

    def _mock() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "trade_date": [
                    "2026-03-20",
                    "2026-03-23",
                    "2026-03-24",
                    "2026-03-25",
                    "2026-03-26",
                    "2026-03-27",
                ]
            }
        )

    monkeypatch.setattr(ak, "tool_trade_date_hist_sina", _mock)


@pytest.fixture
def mock_fund_code_search(monkeypatch: pytest.MonkeyPatch) -> None:
    """mock 东方财富基金代码搜索文件（含货币基金用于排除测试）。"""
    import requests

    content = (
        "var r = ["
        '["510050","ZZ500ETF","华夏上证50ETF","指数型-股票","HUA50"],'
        '["513050","ZGWLB50ETF","易方达中概互联网50ETF","指数型-股票","ZGWLB50"],'
        '["518880","GJJETF","国泰黄金ETF","商品型","GJJ"],'
        '["511690","HTHBJJ","华泰添益货币A","货币型","HTHBJJ"],'
        '["161725","ZZBJZSLOF","招商中证白酒指数LOF","指数型-股票","ZZBJZSLOF"],'
        '["000001","HXCZHH","华夏成长混合","混合型-灵活","HXCZHH"],'
        '["510051","LJ50","华夏上证50ETF联接A","指数型-股票","LJ50"]'
        "];"
    )

    class MockResponse:
        status_code = 200
        text = content

    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: MockResponse(),
    )
