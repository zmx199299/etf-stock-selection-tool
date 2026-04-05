import pytest

from engine.seed_sync import (
    PROJECT_TARGET_FUNDS,
    classify_exchange_symbol,
    build_seed_fund_records,
    normalize_sina_daily_quotes,
    normalize_nav_history,
)


def test_classify_exchange_symbol_prefers_sh_for_5_prefix_codes():
    assert classify_exchange_symbol("510300") == "sh510300"
    assert classify_exchange_symbol("588000") == "sh588000"


def test_classify_exchange_symbol_prefers_sz_for_1_prefix_codes():
    assert classify_exchange_symbol("159915") == "sz159915"
    assert classify_exchange_symbol("161005") == "sz161005"


def test_build_seed_fund_records_uses_real_name_map_and_target_metadata():
    name_map = {item["code"]: f"基金{item['code']}" for item in PROJECT_TARGET_FUNDS}
    name_map["510300"] = "沪深300ETF华泰柏瑞"
    name_map["161005"] = "富国天惠成长混合(LOF)A"

    records = build_seed_fund_records(name_map)
    record_map = {item["code"]: item for item in records}

    assert record_map["510300"]["name"] == "沪深300ETF华泰柏瑞"
    assert record_map["510300"]["fund_type"] == "ETF"
    assert record_map["510300"]["t_plus"] == "T+1"
    assert record_map["161005"]["name"] == "富国天惠成长混合(LOF)A"
    assert record_map["161005"]["fund_type"] == "LOF"


def test_build_seed_fund_records_requires_all_target_codes_present():
    with pytest.raises(ValueError):
        build_seed_fund_records({"510300": "沪深300ETF华泰柏瑞"})


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


def test_project_target_funds_covers_all_explicit_project_targets():
    codes = [item["code"] for item in PROJECT_TARGET_FUNDS]
    assert len(codes) == 27
    assert len(set(codes)) == 27
    assert "510300" in codes
    assert "513130" in codes
    assert "161005" in codes
