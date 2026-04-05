import pytest

from engine.seed_sync import (
    classify_exchange_symbol,
    build_full_market_fund_records,
    is_excluded_fund_type,
    normalize_latest_nav_snapshots,
    normalize_sina_daily_quotes,
    normalize_nav_history,
)


def test_classify_exchange_symbol_prefers_sh_for_5_prefix_codes():
    assert classify_exchange_symbol("510300") == "sh510300"
    assert classify_exchange_symbol("588000") == "sh588000"


def test_classify_exchange_symbol_prefers_sz_for_1_prefix_codes():
    assert classify_exchange_symbol("159915") == "sz159915"
    assert classify_exchange_symbol("161005") == "sz161005"


def test_is_excluded_fund_type_only_filters_money_and_bond_like_types():
    assert is_excluded_fund_type("货币型-普通货币") is True
    assert is_excluded_fund_type("指数型-固收") is True
    assert is_excluded_fund_type("债券型-长债") is True
    assert is_excluded_fund_type("指数型-股票") is False
    assert is_excluded_fund_type("指数型-海外股票") is False
    assert is_excluded_fund_type("指数型-其他") is False


def test_build_full_market_fund_records_filters_by_real_fund_type():
    name_rows = [
        {"基金代码": "159399", "基金简称": "现金流ETF国泰", "基金类型": "指数型-股票"},
        {"基金代码": "159972", "基金简称": "5年地方债ETF鹏华", "基金类型": "指数型-固收"},
        {"基金代码": "161725", "基金简称": "招商中证白酒指数(LOF)A", "基金类型": "指数型-股票"},
    ]
    etf_rows = [
        {"代码": "sz159399", "名称": "现金流ETF国泰"},
        {"代码": "sz159972", "名称": "5年地方债ETF鹏华"},
    ]
    lof_rows = [{"代码": "sz161725", "名称": "招商中证白酒指数LOF"}]

    records = build_full_market_fund_records(name_rows, etf_rows, lof_rows)
    codes = [item["code"] for item in records]
    record_map = {item["code"]: item for item in records}

    assert "159399" in codes
    assert "159972" not in codes
    assert "161725" in codes
    assert record_map["159399"]["fund_type"] == "ETF"
    assert record_map["161725"]["fund_type"] == "LOF"


def test_build_full_market_fund_records_accepts_fallback_metadata_for_missing_name_table_item():
    name_rows = []
    etf_rows = []
    lof_rows = [{"代码": "sz501023", "名称": "港中小企LOF"}]
    fallback_details = {
        "501023": {"name": "鹏华香港中小企业指数LOF", "fund_type_raw": "指数型-股票"}
    }

    records = build_full_market_fund_records(name_rows, etf_rows, lof_rows, fallback_details)

    assert len(records) == 1
    assert records[0]["code"] == "501023"
    assert records[0]["fund_type"] == "LOF"


def test_normalize_sina_daily_quotes_maps_to_database_shape():
    rows = [
        {
            "date": "2026-04-03",
            "open": 4.49,
            "high": 4.50,
            "low": 4.41,
            "close": 4.45,
            "volume": 1000,
            "amount": 2000,
        },
        {
            "date": "2026-04-02",
            "prevclose": 4.53,
            "open": 4.52,
            "high": 4.53,
            "low": 4.47,
            "close": 4.49,
            "volume": 800,
        },
    ]

    normalized = normalize_sina_daily_quotes("510300", rows)

    assert normalized[0]["code"] == "510300"
    assert normalized[0]["date"] == "2026-04-02"
    assert normalized[0]["open"] == pytest.approx(4.52)
    assert normalized[0]["close"] == pytest.approx(4.49)
    assert normalized[0]["high"] == pytest.approx(4.53)
    assert normalized[0]["low"] == pytest.approx(4.47)
    assert normalized[0]["prev_close"] == pytest.approx(4.53)
    assert normalized[1]["date"] == "2026-04-03"
    assert normalized[1]["prev_close"] is None


def test_normalize_nav_history_filters_invalid_rows_and_sorts():
    rows = [
        {"净值日期": "2026-04-03", "单位净值": "1.234"},
        {"净值日期": "", "单位净值": "1.100"},
        {"净值日期": "2026-04-02", "单位净值": 1.2},
    ]

    normalized = normalize_nav_history(rows)

    assert normalized == [
        {"date": "2026-04-02", "nav": pytest.approx(1.2)},
        {"date": "2026-04-03", "nav": pytest.approx(1.234)},
    ]


def test_normalize_latest_nav_snapshots_extracts_latest_date_and_premium_rate():
    rows = [
        {
            "基金代码": "510300",
            "2026-04-03-单位净值": "4.4499",
            "2026-04-02-单位净值": "4.4877",
            "折价率": "-0.09%",
        },
        {
            "基金代码": "161725",
            "2026-04-03-单位净值": "0.6393",
            "2026-04-02-单位净值": "0.6502",
        },
    ]

    snapshots = normalize_latest_nav_snapshots(rows, discount_key="折价率")

    assert snapshots["510300"]["date"] == "2026-04-03"
    assert snapshots["510300"]["nav"] == pytest.approx(4.4499)
    assert snapshots["510300"]["premium_rate"] == pytest.approx(0.0009)
    assert snapshots["161725"]["premium_rate"] is None


def test_build_full_market_fund_records_marks_zero_volume_funds():
    name_rows = [
        {"基金代码": "161725", "基金简称": "招商中证白酒指数(LOF)A", "基金类型": "指数型-股票"},
        {"基金代码": "160137", "基金简称": "南方中证互联网指数(LOF)A", "基金类型": "指数型-股票"},
    ]
    etf_rows = []
    lof_rows = [
        {"代码": "sz161725", "名称": "招商中证白酒指数LOF", "最新价": 1.5, "成交量": 10000},
        {"代码": "sz160137", "名称": "互联基金", "最新价": 0.0, "成交量": 0},
    ]

    records = build_full_market_fund_records(name_rows, etf_rows, lof_rows)
    record_map = {item["code"]: item for item in records}

    assert record_map["161725"]["has_market_data"] == 1
    assert record_map["160137"]["has_market_data"] == 0
