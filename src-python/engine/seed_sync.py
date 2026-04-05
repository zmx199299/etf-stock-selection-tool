from __future__ import annotations

from engine.data.akshare_source import classify_invest_type, classify_t_plus


EXCLUDED_FUND_TYPE_KEYWORDS = ("货币", "固收", "债")


def normalize_fund_code(value) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) >= 6:
        return digits[-6:]
    return ""


def classify_exchange_symbol(code: str) -> str:
    if code.startswith(("50", "51", "52", "58")):
        return f"sh{code}"
    return f"sz{code}"


def is_excluded_fund_type(raw_fund_type: str) -> bool:
    return any(keyword in str(raw_fund_type or "") for keyword in EXCLUDED_FUND_TYPE_KEYWORDS)


def build_full_market_fund_records(
    name_rows: list[dict],
    etf_rows: list[dict],
    lof_rows: list[dict],
    fallback_details: dict[str, dict] | None = None,
) -> list[dict]:
    fallback_details = fallback_details or {}

    name_map = {}
    for row in name_rows:
        code = normalize_fund_code(row.get("基金代码"))
        if not code:
            continue
        name_map[code] = {
            "name": str(row.get("基金简称", "")).strip(),
            "fund_type_raw": str(row.get("基金类型", "")).strip(),
        }

    records_by_code = {}

    def add_rows(rows: list[dict], market_label: str):
        for row in rows:
            code = normalize_fund_code(row.get("代码"))
            if not code:
                continue

            market_name = str(row.get("名称", "")).strip()
            meta = name_map.get(code) or fallback_details.get(code)
            if meta is None:
                raise ValueError(f"missing metadata for market fund: {code}")

            raw_fund_type = str(meta.get("fund_type_raw", "")).strip()
            if is_excluded_fund_type(raw_fund_type):
                continue

            name = str(meta.get("name") or market_name).strip()

            latest_price = float(row.get("最新价", 0) or 0)
            volume = float(row.get("成交量", 0) or 0)
            has_market_data = 1 if (latest_price > 0 or volume > 0) else 0

            records_by_code[code] = {
                "code": code,
                "name": name,
                "fund_type": market_label,
                "invest_type": classify_invest_type(name),
                "t_plus": classify_t_plus(name),
                "list_date": "",
                "is_excluded": 0,
                "has_market_data": has_market_data,
            }

    add_rows(etf_rows, "ETF")
    add_rows(lof_rows, "LOF")

    return [records_by_code[code] for code in sorted(records_by_code)]


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
        if not date or nav in (None, "", "---"):
            continue
        normalized.append({"date": date, "nav": float(nav)})
    normalized.sort(key=lambda item: item["date"])
    return normalized


def normalize_latest_nav_snapshots(rows: list[dict], discount_key: str | None = None) -> dict[str, dict]:
    snapshots = {}

    for row in rows:
        code = normalize_fund_code(row.get("基金代码"))
        if not code:
            continue

        nav_candidates = []
        for key, value in row.items():
            if str(key).endswith("-单位净值"):
                nav_candidates.append((str(key)[:10], value))

        latest_date = None
        latest_nav = None
        for date, value in sorted(nav_candidates, key=lambda item: item[0], reverse=True):
            if value in (None, "", "---"):
                continue
            latest_date = date
            latest_nav = float(value)
            break

        if latest_date is None or latest_nav is None:
            continue

        premium_rate = None
        if discount_key:
            discount_value = row.get(discount_key)
            if discount_value not in (None, "", "---"):
                discount_text = str(discount_value).replace("%", "").strip()
                if discount_text:
                    premium_rate = -float(discount_text) / 100

        snapshots[code] = {
            "date": latest_date,
            "nav": latest_nav,
            "premium_rate": premium_rate,
        }

    return snapshots
