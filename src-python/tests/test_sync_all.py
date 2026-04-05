from pathlib import Path
import importlib.util

from engine.models.database import Database


def _load_sync_all_module():
    module_path = Path(__file__).resolve().parents[1] / "sync_all.py"
    spec = importlib.util.spec_from_file_location("sync_all_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sync_full_market_funds_persists_quotes_and_latest_nav(tmp_path, monkeypatch):
    module = _load_sync_all_module()

    monkeypatch.setattr(
        module,
        "load_name_rows",
        lambda: [
            {"基金代码": "510300", "基金简称": "沪深300ETF华泰柏瑞", "基金类型": "指数型-股票"},
            {"基金代码": "161725", "基金简称": "招商中证白酒指数(LOF)A", "基金类型": "指数型-股票"},
            {"基金代码": "159972", "基金简称": "5年地方债ETF鹏华", "基金类型": "指数型-固收"},
        ],
    )
    monkeypatch.setattr(
        module,
        "load_etf_rows",
        lambda: [
            {"代码": "sh510300", "名称": "沪深300ETF华泰柏瑞", "最新价": 4.5, "成交量": 10000},
            {"代码": "sz159972", "名称": "5年地方债ETF鹏华", "最新价": 1.0, "成交量": 5000},
        ],
    )
    monkeypatch.setattr(
        module,
        "load_lof_rows",
        lambda: [{"代码": "sz161725", "名称": "招商中证白酒指数LOF", "最新价": 0.64, "成交量": 8000}],
    )
    monkeypatch.setattr(module, "load_fallback_details", lambda: {})
    monkeypatch.setattr(
        module,
        "fetch_market_quotes",
        lambda code: [
            {
                "code": code,
                "date": "2026-04-03",
                "open": 1.0,
                "close": 1.1,
                "high": 1.2,
                "low": 0.9,
                "volume": 1000.0,
                "amount": 2000.0,
                "nav": None,
                "premium_rate": None,
                "prev_close": 0.95,
                "is_suspended": 0,
                "suspended_days": 0,
            }
        ],
    )
    monkeypatch.setattr(
        module,
        "load_latest_nav_snapshots",
        lambda: {
            "510300": {"date": "2026-04-03", "nav": 4.4499, "premium_rate": 0.0009},
            "161725": {"date": "2026-04-03", "nav": 0.6393, "premium_rate": None},
        },
    )

    db = Database(str(tmp_path / "full.db"))
    db.init()
    try:
        fund_count, quotes_count, nav_count, skipped_count = module.sync_full_market_funds(db)
        assert fund_count == 2
        assert quotes_count == 2
        assert nav_count == 2
        assert skipped_count == 0

        funds = db.get_all_active_funds()
        codes = [item["code"] for item in funds]
        assert codes == ["161725", "510300"]

        quotes = db.get_daily_quotes("510300", "2026-04-03", "2026-04-03")
        assert len(quotes) == 1
        assert quotes[0]["nav"] == 4.4499
        assert quotes[0]["premium_rate"] == 0.0009

        nav_rows = db.get_fund_nav_history("161725", "2026-04-03", "2026-04-03")
        assert len(nav_rows) == 1
        assert nav_rows[0]["nav"] == 0.6393
    finally:
        db.close()


def test_sync_skips_funds_without_market_data(tmp_path, monkeypatch):
    module = _load_sync_all_module()

    monkeypatch.setattr(
        module,
        "load_name_rows",
        lambda: [
            {"基金代码": "510300", "基金简称": "沪深300ETF华泰柏瑞", "基金类型": "指数型-股票"},
            {"基金代码": "160137", "基金简称": "南方中证互联网指数(LOF)A", "基金类型": "指数型-股票"},
        ],
    )
    monkeypatch.setattr(
        module,
        "load_etf_rows",
        lambda: [{"代码": "sh510300", "名称": "沪深300ETF华泰柏瑞", "最新价": 4.5, "成交量": 10000}],
    )
    monkeypatch.setattr(
        module,
        "load_lof_rows",
        lambda: [{"代码": "sz160137", "名称": "互联基金", "最新价": 0.0, "成交量": 0}],
    )
    monkeypatch.setattr(module, "load_fallback_details", lambda: {})

    fetch_calls = []

    def mock_fetch(code):
        fetch_calls.append(code)
        return [{"code": code, "date": "2026-04-03", "open": 1.0, "close": 1.1, "high": 1.2, "low": 0.9, "volume": 1000.0, "amount": 2000.0, "nav": None, "premium_rate": None, "prev_close": 0.95, "is_suspended": 0, "suspended_days": 0}]

    monkeypatch.setattr(module, "fetch_market_quotes", mock_fetch)
    monkeypatch.setattr(
        module,
        "load_latest_nav_snapshots",
        lambda: {
            "510300": {"date": "2026-04-03", "nav": 4.4499, "premium_rate": 0.0009},
            "160137": {"date": "2026-04-03", "nav": 1.5894, "premium_rate": None},
        },
    )

    db = Database(str(tmp_path / "skip_test.db"))
    db.init()
    try:
        fund_count, quotes_count, nav_count, skipped_count = module.sync_full_market_funds(db)
        assert fund_count == 2
        assert quotes_count == 1
        assert nav_count == 2
        assert skipped_count == 1
        assert fetch_calls == ["510300"]
        assert "160137" not in fetch_calls

        fund_160137 = db.get_fund_info("160137")
        assert fund_160137["has_market_data"] == 0
    finally:
        db.close()
