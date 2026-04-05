"""
场内基金V型反转筛选工具

每天收盘后运行，筛选符合日内V型反转条件的场内基金（ETF/LOF），
标注T+0/T+1属性，结合技术指标预测次日买入价值，
判断下一交易日是否停牌。
"""

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
import requests
import ta

# ── 日志配置 ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── 常量 ──────────────────────────────────────────────────────────────────────
CONSECUTIVE_DAYS = 3  # 连续满足条件的天数
AMPLITUDE_MIN = 3.5  # 振幅下限（%）
AMPLITUDE_MAX = 4.5  # 振幅上限（%）
LOW_DROP_MIN = 1.0  # 最低点相对昨收下跌最小幅度（%）
BUY_SCORE_THRESHOLD = 60  # 买入评分阈值
RETRY_TIMES = 3  # API 最大重试次数
REQUEST_TIMEOUT = 15  # 请求超时（秒）
MAX_WORKERS = 20  # 并发线程数（历史K线批量请求）
SUSPEND_BATCH_SIZE = 200  # 停牌查询每批基金数量

# 请求头
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# T+0 判断关键词（基金名称包含以下任意关键词则为T+0）
T0_KEYWORDS = [
    "跨境",
    "港股",
    "恒生",
    "纳斯达克",
    "标普",
    "德国",
    "日经",
    "黄金",
    "白银",
    "原油",
    "商品",
    "豆粕",
    "有色",
    "能源",
    "债券",
    "国债",
    "短融",
    "信用",
    "可转债",
    "货币",
    "添益",
    "日利",
    "互联网",
    "油气",
]

# 历史数据请求时往前多取的天数（应对节假日）
HIST_LOOKBACK_DAYS = 30


# ── 交易日历 ──────────────────────────────────────────────────────────────────


def get_trade_calendar() -> list[str]:
    """
    获取完整A股交易日历。

    Returns:
        交易日字符串列表，格式 'YYYY-MM-DD'，升序排列。
        失败时返回简单排除周末的近60天列表（fallback）。
    """
    for attempt in range(RETRY_TIMES):
        try:
            df = ak.tool_trade_date_hist_sina()
            col = df.columns[0]
            dates = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d").tolist()
            logger.info(f"交易日历加载成功，共 {len(dates)} 个交易日")
            return sorted(dates)
        except Exception as e:
            logger.warning(f"获取交易日历失败（第{attempt + 1}次）：{e}")

    logger.warning("交易日历获取失败，使用简单排除周末的 fallback 数据")
    today = datetime.now().date()
    fallback: list[str] = []
    d = today - timedelta(days=60)
    while d <= today:
        if d.weekday() < 5:
            fallback.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return fallback


def get_latest_trade_date(calendar: list[str]) -> str:
    """
    根据当前时间和交易日历，返回应使用数据的交易日。

    交易时段（9:30-15:00，含午休）→ 使用前一交易日数据；
    其余时段 → 使用最近交易日数据。

    Args:
        calendar: 交易日字符串列表（升序）。

    Returns:
        目标交易日字符串，格式 'YYYY-MM-DD'。
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    hour, minute = now.hour, now.minute

    in_trading_session = not ((hour < 9) or (hour == 9 and minute < 30) or (hour >= 15))

    past_dates = [d for d in calendar if d <= today_str]
    if not past_dates:
        return today_str

    if in_trading_session:
        if len(past_dates) >= 2:
            return past_dates[-2]
        return past_dates[-1]
    else:
        return past_dates[-1]


def get_next_trade_date(calendar: list[str], base_date: str) -> str | None:
    """
    获取指定日期的下一个交易日。

    Args:
        calendar: 交易日字符串列表（升序）。
        base_date: 基准日期，格式 'YYYY-MM-DD'。

    Returns:
        下一交易日字符串，或 None（若不存在）。
    """
    future = [d for d in calendar if d > base_date]
    return future[0] if future else None


# ── 基金列表 ──────────────────────────────────────────────────────────────────


def get_all_funds() -> dict[str, str]:
    """
    从东方财富获取全量场内 ETF 和 LOF 列表。

    使用 fund.eastmoney.com/js/fundcode_search.js 获取全部基金，
    然后按代码前缀和名称筛选场内可交易基金。

    Returns:
        字典 {基金代码: 基金名称}。
        失败时返回少量示例数据（fallback）。
    """
    for attempt in range(RETRY_TIMES):
        try:
            r = requests.get(
                "https://fund.eastmoney.com/js/fundcode_search.js",
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code != 200:
                continue

            # 格式: [["000001","ABBR","基金名称","类型","英文名"], ...]
            match = re.search(r"var r = (\[.*?\]);", r.text, re.DOTALL)
            if not match:
                continue

            raw_list = json.loads(match.group(1))
            fund_dict: dict[str, str] = {}

            for item in raw_list:
                code = str(item[0]).zfill(6)
                name = item[2]

                fund_type = item[3]

                # 筛选场内基金：排除联接基金、货币基金，仅保留以下代码段：
                # 上证: 50xxxx ~ 59xxxx（含 ETF、LOF）
                # 深证: 15xxxx（ETF）、16xxxx（LOF）
                if "联接" in name:
                    continue
                if "货币" in name or "货币" in fund_type:
                    continue
                if not code.startswith(
                    (
                        "50",
                        "51",
                        "52",
                        "53",
                        "54",
                        "55",
                        "56",
                        "57",
                        "58",
                        "59",
                        "15",
                        "16",
                    )
                ):
                    continue

                fund_dict[code] = name

            if fund_dict:
                logger.info(
                    f"场内基金列表加载成功，共 {len(fund_dict)} 只（ETF + LOF）"
                )
                return fund_dict

        except Exception as e:
            logger.warning(f"获取基金列表失败（第{attempt + 1}次）：{e}")

    logger.warning("基金列表获取失败，使用 fallback 示例数据")
    return {
        "510050": "华夏上证50ETF",
        "510300": "华泰柏瑞沪深300ETF",
        "510500": "南方中证500ETF",
        "161725": "招商中证白酒指数LOF",
        "160706": "嘉实沪深300LOF",
    }


def is_t0(fund_name: str) -> bool:
    """
    判断基金是否为 T+0 交易制度。

    Args:
        fund_name: 基金名称。

    Returns:
        True 表示 T+0，False 表示 T+1。
    """
    return any(kw in fund_name for kw in T0_KEYWORDS)


# ── 历史行情 ──────────────────────────────────────────────────────────────────


def _tencent_symbol(code: str) -> str:
    """将 6 位基金代码转换为腾讯行情前缀（sh/sz）。"""
    if code.startswith(("5", "6")):
        return f"sh{code}"
    return f"sz{code}"


def get_fund_hist(
    code: str,
    name: str,
    latest_date: str,
) -> pd.DataFrame | None:
    """
    获取单只基金最近若干交易日的历史行情。

    使用腾讯财经前复权日K线 API 获取 OHLCV 数据。
    数据格式：[日期, 开盘, 收盘, 最高, 最低, 成交量]

    Args:
        code: 基金代码。
        name: 基金名称（仅用于日志）。
        latest_date: 最新目标交易日，格式 'YYYY-MM-DD'。

    Returns:
        处理后的 DataFrame（已按日期升序排列），或 None。
    """
    symbol = _tencent_symbol(code)
    # 往前取足够多的天数（CONSECUTIVE_DAYS+1 行情 + 技术指标需要 ≥26 行）
    # 腾讯 API 最多返回指定 count 条，往前推 60 天足够
    start_date = (
        datetime.strptime(latest_date, "%Y-%m-%d") - timedelta(days=60)
    ).strftime("%Y-%m-%d")

    for attempt in range(RETRY_TIMES):
        try:
            r = requests.get(
                "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                params={
                    "param": f"{symbol},day,{start_date},{latest_date},60,qfq",
                    "_var": "kline_dayfqk",
                },
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            if r.status_code != 200:
                continue

            # 去掉 JSONP 前缀解析
            json_str = re.sub(r"^kline_dayfqk=", "", r.text)
            data = json.loads(json_str)
            fund_data = data.get("data", {}).get(symbol, {})
            # 前复权用 qfqday，若无则退回 day
            klines = fund_data.get("qfqday") or fund_data.get("day", [])

            if not klines:
                continue

            rows = []
            for bar in klines:
                # 腾讯格式：[日期, 开盘, 收盘, 最高, 最低, 成交量]
                rows.append(
                    {
                        "date": bar[0],
                        "开盘": float(bar[1]),
                        "收盘": float(bar[2]),
                        "最高": float(bar[3]),
                        "最低": float(bar[4]),
                        "成交量": int(float(bar[5])),
                    }
                )

            df = pd.DataFrame(rows)
            df = df.sort_values("date").reset_index(drop=True)

            if df["date"].iloc[-1] < latest_date:
                logger.debug(
                    f"跳过 {code}（{name}）：最新数据 {df['date'].iloc[-1]} "
                    f"早于目标日期 {latest_date}"
                )
                return None

            return df

        except Exception as e:
            logger.debug(f"获取 {code} 历史数据失败（第{attempt + 1}次）：{e}")

    logger.debug(f"跳过 {code}（{name}）：无历史数据")
    return None


def fetch_all_fund_hist(
    fund_dict: dict[str, str],
    latest_date: str,
) -> dict[str, pd.DataFrame]:
    """
    并发批量获取全量基金历史行情。

    使用线程池并发请求腾讯财经 K 线 API，大幅缩短整体耗时。

    Args:
        fund_dict: 字典 {基金代码: 基金名称}。
        latest_date: 最新目标交易日，格式 'YYYY-MM-DD'。

    Returns:
        字典 {基金代码: DataFrame}，仅含成功获取且数据有效的基金。
    """
    result: dict[str, pd.DataFrame] = {}

    def _fetch(code: str, name: str) -> tuple[str, pd.DataFrame | None]:
        return code, get_fund_hist(code, name, latest_date)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_fetch, code, name): code
            for code, name in fund_dict.items()
        }
        done_count = 0
        total = len(futures)
        for future in as_completed(futures):
            done_count += 1
            if done_count % 200 == 0:
                logger.info(f"历史数据进度：{done_count}/{total}")
            try:
                code, df = future.result()
                if df is not None:
                    result[code] = df
            except Exception as e:
                logger.debug(f"并发获取历史数据异常：{e}")

    logger.info(f"历史数据加载完成，有效基金 {len(result)}/{total} 只")
    return result


# ── 筛选逻辑 ──────────────────────────────────────────────────────────────────


def check_v_reversal(df: pd.DataFrame, latest_date: str) -> bool:
    """
    判断基金是否在最近 CONSECUTIVE_DAYS 个交易日内连续满足V型反转条件。

    条件：
      1. 振幅（最高-最低）/昨收 在 [AMPLITUDE_MIN, AMPLITUDE_MAX]
      2. 当日最低 相对昨收 下跌 ≥ LOW_DROP_MIN %
      3. 最高点 > 最低点（V型，即当日有反弹）

    Args:
        df: 历史行情 DataFrame，含 date/开盘/收盘/最高/最低/成交量。
        latest_date: 最新目标交易日，格式 'YYYY-MM-DD'。

    Returns:
        True 表示连续满足，False 表示不满足。
    """
    sub = df[df["date"] <= latest_date].tail(CONSECUTIVE_DAYS + 1).copy()
    if len(sub) < CONSECUTIVE_DAYS + 1:
        return False

    rows = sub.reset_index(drop=True)
    eps = 1e-6

    for i in range(1, CONSECUTIVE_DAYS + 1):
        row = rows.iloc[i]
        prev_close = float(rows.iloc[i - 1]["收盘"])
        if prev_close <= 0:
            return False

        high = float(row["最高"])
        low = float(row["最低"])

        amplitude = (high - low) / prev_close * 100
        low_drop = (low - prev_close) / prev_close * 100

        if not (AMPLITUDE_MIN - eps <= amplitude <= AMPLITUDE_MAX + eps):
            return False
        if low_drop > -LOW_DROP_MIN + eps:
            return False
        if high <= low:
            return False

    return True


# ── 技术指标评分 ──────────────────────────────────────────────────────────────


def calc_buy_score(df: pd.DataFrame, latest_date: str) -> int:
    """
    计算次日买入价值评分（0-100分）。

    评分项：
      - RSI(14) < 30：+25分；30-40：+15分
      - MACD 金叉（DIF上穿DEA）：+25分
      - 布林带 价格<下轨：+20分；接近下轨（<下轨+带宽*0.1）：+10分
      - MA5/10/20 多头排列：+15分
      - 成交量放量（最新量>5日均量*1.5）：+10分
      - V型反转特征（满足筛选条件固定加分）：+15分

    Args:
        df: 历史行情 DataFrame。
        latest_date: 最新目标交易日，格式 'YYYY-MM-DD'。

    Returns:
        整数评分（0-100）。
    """
    sub = df[df["date"] <= latest_date].copy()
    if len(sub) < 26:
        return 0

    close = sub["收盘"].astype(float)
    volume = sub["成交量"].astype(float)
    score = 0

    # RSI
    try:
        rsi_val = ta.momentum.RSIIndicator(close=close, window=14).rsi().iloc[-1]
        if rsi_val < 30:
            score += 25
        elif rsi_val < 40:
            score += 15
    except Exception:
        pass

    # MACD 金叉
    try:
        macd_ind = ta.trend.MACD(
            close=close, window_slow=26, window_fast=12, window_sign=9
        )
        dif = macd_ind.macd()
        dea = macd_ind.macd_signal()
        if (
            len(dif) >= 2
            and dif.iloc[-2] <= dea.iloc[-2]
            and dif.iloc[-1] > dea.iloc[-1]
        ):
            score += 25
    except Exception:
        pass

    # 布林带
    try:
        bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
        lower = bb.bollinger_lband().iloc[-1]
        upper = bb.bollinger_hband().iloc[-1]
        price = close.iloc[-1]
        band_width = upper - lower
        if price < lower:
            score += 20
        elif band_width > 0 and price < lower + band_width * 0.1:
            score += 10
    except Exception:
        pass

    # 均线多头排列
    try:
        ma5 = close.rolling(5).mean().iloc[-1]
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        if ma5 > ma10 > ma20:
            score += 15
    except Exception:
        pass

    # 成交量放量
    try:
        vol_ma5 = volume.rolling(5).mean().iloc[-1]
        vol_latest = volume.iloc[-1]
        if vol_ma5 > 0 and vol_latest > vol_ma5 * 1.5:
            score += 10
    except Exception:
        pass

    # V型反转特征
    score += 15

    return min(score, 100)


# ── 停牌判断 ──────────────────────────────────────────────────────────────────


def get_suspended_funds(
    next_trade_date: str,
    fund_codes: list[str] | None = None,
) -> set[str]:
    """
    获取指定交易日停牌的基金代码集合。

    通过腾讯财经实时行情批量接口查询，若基金当日价格为 0 或无数据，
    则判定为停牌。ETF/LOF 基金很少停牌，此方法可有效兜底。

    注：仅当 fund_codes 非空时才进行网络查询；若 fund_codes 为空，直接返回空集合。

    Args:
        next_trade_date: 下一交易日，格式 'YYYY-MM-DD'（仅用于日志）。
        fund_codes: 需要检查的基金代码列表（6位字符串）。
                    若为 None 则跳过查询返回空集合。

    Returns:
        停牌基金代码的集合（6位字符串）。
    """
    if not fund_codes:
        return set()

    suspended: set[str] = set()
    codes_list = list(fund_codes)

    # 分批查询，每批 SUSPEND_BATCH_SIZE 只
    for batch_start in range(0, len(codes_list), SUSPEND_BATCH_SIZE):
        batch = codes_list[batch_start : batch_start + SUSPEND_BATCH_SIZE]
        tencent_codes = [_tencent_symbol(c) for c in batch]
        query = ",".join(tencent_codes)

        for attempt in range(RETRY_TIMES):
            try:
                r = requests.get(
                    f"https://qt.gtimg.cn/q={query}",
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                if r.status_code != 200:
                    continue

                # 解析响应：每行一只基金
                # 格式：v_sh510050="1~名称~代码~当前价~..."
                for line in r.text.strip().split(";"):
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    try:
                        value_part = line.split("=", 1)[1].strip('"')
                        fields = value_part.split("~")
                        if len(fields) < 4:
                            continue
                        raw_code = fields[2].strip().zfill(6)
                        price_str = fields[3].strip()
                        # 价格为空或 0 视为停牌
                        price = float(price_str) if price_str else 0.0
                        if price <= 0:
                            suspended.add(raw_code)
                            logger.info(
                                f"  检测到停牌：{raw_code}（{next_trade_date}）"
                            )
                    except (ValueError, IndexError):
                        continue
                break  # 本批查询成功，跳出重试
            except Exception as e:
                logger.warning(
                    f"停牌查询失败（第{attempt + 1}次，批次起始{batch_start}）：{e}"
                )

    return suspended


# ── 主流程 ────────────────────────────────────────────────────────────────────


def print_no_result() -> None:
    """输出无结果时的标准说明。"""
    print(
        "\n暂时没有符合条件的基金\n"
        "筛选条件：\n"
        f"  - 日内波动幅度 {AMPLITUDE_MIN}% ~ {AMPLITUDE_MAX}%\n"
        f"  - 当日最低点相对昨收下跌 ≥ {LOW_DROP_MIN}%（先跌）\n"
        "  - 最高点 > 最低点（V型反转）\n"
        f"  - 连续 {CONSECUTIVE_DAYS} 天满足以上条件\n"
        f"  - 次日买入价值评分 ≥ {BUY_SCORE_THRESHOLD} 分\n"
        "  - 下一交易日未停牌\n"
        "  - 非货币基金"
    )


def main() -> None:
    """主入口：加载数据、筛选基金、输出结果。"""
    logger.info("===== 场内基金V型反转筛选工具 =====")

    # 1. 交易日历
    calendar = get_trade_calendar()
    latest_date = get_latest_trade_date(calendar)
    next_date = get_next_trade_date(calendar, latest_date)
    logger.info(f"分析日期：{latest_date}，下一交易日：{next_date}")

    # 2. 基金列表
    fund_dict = get_all_funds()
    logger.info(f"共加载 {len(fund_dict)} 只基金（ETF + LOF）")

    # 3. 并发批量获取历史行情
    all_hist = fetch_all_fund_hist(fund_dict, latest_date)

    # 4. 筛选 V 型反转 + 评分
    candidates: list[dict] = []
    for code, df in all_hist.items():
        name = fund_dict[code]

        if not check_v_reversal(df, latest_date):
            continue

        score = calc_buy_score(df, latest_date)
        if score < BUY_SCORE_THRESHOLD:
            continue

        candidates.append(
            {
                "code": code,
                "name": name,
                "t0": is_t0(name),
                "score": score,
                "next_date": next_date or "未知",
            }
        )

    logger.info(f"V型反转初步筛选：{len(candidates)} 只候选基金")

    # 5. 仅对候选基金做停牌查询（减少无谓请求）
    suspended: set[str] = set()
    if next_date and candidates:
        candidate_codes = [c["code"] for c in candidates]
        suspended = get_suspended_funds(next_date, candidate_codes)
        logger.info(f"下一交易日（{next_date}）候选基金中停牌：{len(suspended)} 只")

    # 6. 排除停牌，整理结果
    results = [c for c in candidates if c["code"] not in suspended]
    for c in candidates:
        if c["code"] in suspended:
            logger.info(f"  排除 {c['code']}（{c['name']}）：下一交易日停牌")

    # 7. 输出结果
    if not results:
        print_no_result()
        return

    print(f"\n共找到 {len(results)} 只符合条件的场内基金：\n")
    print(f"{'代码':<8} {'名称':<25} {'T+0/T+1':<8} {'评分':<6} {'下一交易日'}")
    print("-" * 65)
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        t_flag = "T+0" if r["t0"] else "T+1"
        print(
            f"{r['code']:<8} {r['name']:<25} {t_flag:<8} {r['score']:<6} {r['next_date']}"
        )


if __name__ == "__main__":
    main()
