from __future__ import annotations


PROJECT_TARGET_FUNDS = [
    {"code": "161005", "fund_type": "LOF", "invest_type": "股票型", "t_plus": "T+1"},
    {"code": "161725", "fund_type": "LOF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "159869", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "159915", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "159919", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "159920", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "159928", "fund_type": "ETF", "invest_type": "消费主题型", "t_plus": "T+1"},
    {"code": "159941", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "159995", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "510050", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "510300", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "510500", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
    {"code": "512000", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "512170", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "512480", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "512660", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "512880", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "512890", "fund_type": "ETF", "invest_type": "红利主题型", "t_plus": "T+1"},
    {"code": "512980", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "513030", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "513050", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "513100", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "513130", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "513500", "fund_type": "ETF", "invest_type": "跨境型(QDII)", "t_plus": "T+0"},
    {"code": "515790", "fund_type": "ETF", "invest_type": "行业主题型", "t_plus": "T+1"},
    {"code": "518880", "fund_type": "ETF", "invest_type": "商品型", "t_plus": "T+0"},
    {"code": "588000", "fund_type": "ETF", "invest_type": "指数型", "t_plus": "T+1"},
]


def classify_exchange_symbol(code: str) -> str:
    if code.startswith(("50", "51", "52", "58")):
        return f"sh{code}"
    return f"sz{code}"


def build_seed_fund_records(name_map: dict[str, str]) -> list[dict]:
    missing = [item["code"] for item in PROJECT_TARGET_FUNDS if item["code"] not in name_map]
    if missing:
        raise ValueError(f"missing fund names for target codes: {', '.join(missing)}")

    records = []
    for item in PROJECT_TARGET_FUNDS:
        records.append(
            {
                "code": item["code"],
                "name": name_map[item["code"]],
                "fund_type": item["fund_type"],
                "invest_type": item["invest_type"],
                "t_plus": item["t_plus"],
                "list_date": "",
                "is_excluded": 0,
            }
        )
    return records


def normalize_sina_daily_quotes(code: str, rows: list[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        date = str(row.get("date", ""))[:10]
        if not date:
            continue
        normalized.append(
            {
                "code": code,
                "date": date,
                "open": float(row.get("open", 0) or 0),
                "close": float(row.get("close", 0) or 0),
                "high": float(row.get("high", 0) or 0),
                "low": float(row.get("low", 0) or 0),
                "volume": float(row.get("volume", 0) or 0),
                "amount": float(row.get("amount", 0) or 0),
                "nav": None,
                "premium_rate": None,
                "prev_close": float(row.get("prevclose")) if row.get("prevclose") not in (None, "") else None,
                "is_suspended": 0,
                "suspended_days": 0,
            }
        )
    normalized.sort(key=lambda item: item["date"])
    return normalized


def normalize_nav_history(rows: list[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        date = str(row.get("净值日期", ""))[:10]
        nav = row.get("单位净值")
        if not date or nav in (None, ""):
            continue
        normalized.append({"date": date, "nav": float(nav)})
    normalized.sort(key=lambda item: item["date"])
    return normalized
