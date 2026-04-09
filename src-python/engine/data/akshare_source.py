# src-python/engine/data/akshare_source.py
"""多源容错数据源：并发尝试东方财富(_em)和新浪(_sina)接口，取数量多的结果。
单只基金的数据抓取失败时自动切换备用源。"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import akshare as ak
import pandas as pd
from .base import DataSource

logger = logging.getLogger(__name__)

# T+0 基金关键词（跨境、货币、债券、黄金、商品类ETF支持T+0）
T0_KEYWORDS = [
    "跨境",
    "QDII",
    "黄金",
    "商品",
    "货币",
    "债券",
    "油",
    "铜",
    "豆粕",
    "标普",
    "纳指",
    "恒生",
    "日经",
    "港股",
]
# 排除关键词
EXCLUDE_KEYWORDS_MONEY = ["货币", "理财", "现金"]
EXCLUDE_KEYWORDS_BOND = ["债券", "债", "利率", "城投"]
# 投资类别映射关键词
INVEST_TYPE_MAP = [
    (
        ["跨境", "QDII", "纳指", "标普", "日经", "恒生", "港股", "德国", "法国"],
        "跨境型(QDII)",
    ),
    (["黄金", "白银", "油", "铜", "豆粕", "商品", "有色"], "商品型"),
    (["REITs", "REIT", "产园", "仓储", "产业园", "高速", "保障房"], "REITs"),
    (
        [
            "行业",
            "主题",
            "科技",
            "医药",
            "消费",
            "军工",
            "新能源",
            "半导体",
            "芯片",
            "光伏",
            "白酒",
            "金融",
            "银行",
            "地产",
            "煤炭",
            "钢铁",
            "农业",
        ],
        "行业主题型",
    ),
    (
        ["沪深300", "中证500", "中证1000", "上证50", "创业板", "科创", "指数", "红利"],
        "指数型",
    ),
]


def classify_invest_type(name: str) -> str:
    for keywords, itype in INVEST_TYPE_MAP:
        if any(kw in name for kw in keywords):
            return itype
    return "股票型"


def classify_t_plus(name: str) -> str:
    if any(kw in name for kw in T0_KEYWORDS):
        return "T+0"
    return "T+1"


def _is_excluded(name: str) -> bool:
    for kw in EXCLUDE_KEYWORDS_MONEY:
        if kw in name:
            return True
    for kw in EXCLUDE_KEYWORDS_BOND:
        if kw in name:
            return True
    return False


def _classify_exchange_symbol(code: str) -> str:
    """根据基金代码判断上交所/深交所前缀（新浪接口需要）"""
    if code.startswith(("50", "51", "52", "58")):
        return f"sh{code}"
    return f"sz{code}"


def _normalize_fund_code(value) -> str:
    """从原始基金代码中提取标准6位数字"""
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) >= 6:
        return digits[-6:]
    return ""


class AkshareSource(DataSource):
    def __init__(self, em_skip_threshold: int = 5):
        """初始化数据源
        Args:
            em_skip_threshold: em 连续失败多少次后跳过 em 直接用 sina
        """
        self._em_consecutive_failures = 0
        self._em_skip_threshold = em_skip_threshold

    # ------------------------------------------------------------------
    # 基金列表：多源并发，取数量多的
    # ------------------------------------------------------------------

    def fetch_fund_list(self) -> list[dict]:
        """并发尝试东方财富和新浪两套接口获取基金列表，取数量最多的结果"""
        results = {}

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {
                pool.submit(self._fetch_fund_list_em): "em",
                pool.submit(self._fetch_fund_list_sina): "sina",
            }
            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    funds = future.result()
                    results[source_name] = funds
                    logger.info(f"数据源 [{source_name}] 返回 {len(funds)} 只基金")
                except Exception as e:
                    logger.warning(f"数据源 [{source_name}] 基金列表获取失败: {e}")

        if not results:
            logger.error("所有数据源均失败，基金列表为空")
            return []

        # 取数量最多的源
        best_source = max(results, key=lambda k: len(results[k]))
        best_funds = results[best_source]
        logger.info(f"选择数据源 [{best_source}]，共 {len(best_funds)} 只基金")
        return best_funds

    def _fetch_fund_list_em(self) -> list[dict]:
        """东方财富源：fund_etf_spot_em + fund_lof_spot_em"""
        try:
            df_etf = ak.fund_etf_spot_em()
        except Exception as e:
            logger.warning(f"fund_etf_spot_em 失败: {e}")
            df_etf = pd.DataFrame()

        try:
            df_lof = ak.fund_lof_spot_em()
        except Exception as e:
            logger.warning(f"fund_lof_spot_em 失败: {e}")
            df_lof = pd.DataFrame()

        funds = []
        for df, ftype in [(df_etf, "ETF"), (df_lof, "LOF")]:
            if df.empty:
                continue
            for _, row in df.iterrows():
                code = str(row.get("代码", "")).strip()
                name = str(row.get("名称", "")).strip()
                if not code or not name:
                    continue
                fund = {
                    "code": code,
                    "name": name,
                    "fund_type": ftype,
                    "invest_type": classify_invest_type(name),
                    "t_plus": classify_t_plus(name),
                    "list_date": "",
                    "is_excluded": 1 if _is_excluded(name) else 0,
                }
                funds.append(fund)
        return funds

    def _fetch_fund_list_sina(self) -> list[dict]:
        """新浪源：fund_etf_category_sina + fund_name_em 交叉引用，
        复用 sync_all.py / seed_sync.py 的过滤逻辑"""
        # 获取基金名称元数据表（用于判断基金类型，过滤货币/债券）
        try:
            name_df = ak.fund_name_em()
            name_rows = name_df.to_dict("records")
        except Exception as e:
            logger.warning(f"fund_name_em 失败: {e}")
            name_rows = []

        name_map = {}
        for row in name_rows:
            code = _normalize_fund_code(row.get("基金代码"))
            if not code:
                continue
            name_map[code] = {
                "name": str(row.get("基金简称", "")).strip(),
                "fund_type_raw": str(row.get("基金类型", "")).strip(),
            }

        # 获取 ETF 和 LOF 列表（新浪源）
        etf_rows = []
        lof_rows = []
        try:
            etf_df = ak.fund_etf_category_sina(symbol="ETF基金")
            etf_rows = etf_df.to_dict("records")
        except Exception as e:
            logger.warning(f"fund_etf_category_sina(ETF) 失败: {e}")

        try:
            lof_df = ak.fund_etf_category_sina(symbol="LOF基金")
            lof_rows = lof_df.to_dict("records")
        except Exception as e:
            logger.warning(f"fund_etf_category_sina(LOF) 失败: {e}")

        # 排除货币/债券型基金的关键词
        excluded_keywords = ("货币", "固收", "债")

        funds = []
        seen_codes = set()

        for rows, market_label in [(etf_rows, "ETF"), (lof_rows, "LOF")]:
            for row in rows:
                code = _normalize_fund_code(row.get("代码"))
                if not code or code in seen_codes:
                    continue
                seen_codes.add(code)

                market_name = str(row.get("名称", "")).strip()
                meta = name_map.get(code)

                # 如果 fund_name_em 也没有这只基金，用市场名称
                if meta:
                    raw_fund_type = meta.get("fund_type_raw", "")
                    name = meta.get("name") or market_name
                    # 按基金类型过滤货币/债券
                    if any(kw in raw_fund_type for kw in excluded_keywords):
                        continue
                else:
                    name = market_name

                latest_price = float(row.get("最新价", 0) or 0)
                volume = float(row.get("成交量", 0) or 0)
                has_market_data = 1 if (latest_price > 0 or volume > 0) else 0

                fund = {
                    "code": code,
                    "name": name,
                    "fund_type": market_label,
                    "invest_type": classify_invest_type(name),
                    "t_plus": classify_t_plus(name),
                    "list_date": "",
                    "is_excluded": 1 if _is_excluded(name) else 0,
                    "has_market_data": has_market_data,
                }
                funds.append(fund)

        return funds

    # ------------------------------------------------------------------
    # 日线行情：先试 _em，失败 fallback 到 _sina
    # ------------------------------------------------------------------

    def fetch_daily_quotes(self, code: str, start_date: str = None) -> list[dict]:
        """先试东方财富日线，失败则 fallback 到新浪日线。
        em 连续失败超过阈值后自动跳过 em，直接用 sina，大幅减少同步耗时。"""
        # em 连续失败过多次，跳过 em 直接用 sina
        if self._em_consecutive_failures >= self._em_skip_threshold:
            return self._fetch_daily_quotes_sina(code, start_date)

        # 第一优先：东方财富
        quotes = self._fetch_daily_quotes_em(code, start_date)
        if quotes:
            # em 成功，重置失败计数
            self._em_consecutive_failures = 0
            return quotes

        # em 失败，计数 +1
        self._em_consecutive_failures += 1
        if self._em_consecutive_failures >= self._em_skip_threshold:
            logger.warning(
                f"em 数据源已连续失败 {self._em_consecutive_failures} 次，"
                f"后续日线将跳过 em 直接使用 sina"
            )

        # Fallback：新浪
        logger.info(f"[{code}] 东方财富日线为空或失败，尝试新浪源...")
        return self._fetch_daily_quotes_sina(code, start_date)

    def _fetch_daily_quotes_em(self, code: str, start_date: str = None) -> list[dict]:
        """东方财富日线：fund_etf_hist_em"""
        try:
            df = ak.fund_etf_hist_em(
                symbol=code,
                period="daily",
                start_date=start_date.replace("-", "") if start_date else "19900101",
                adjust="",
            )
        except Exception as e:
            logger.warning(f"fund_etf_hist_em({code}) 失败: {e}")
            return []
        if df.empty:
            return []
        results = []
        for _, row in df.iterrows():
            results.append(
                {
                    "date": str(row.get("日期", ""))[:10],
                    "open": float(row.get("开盘", 0)),
                    "close": float(row.get("收盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "volume": float(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                }
            )
        return results

    def _fetch_daily_quotes_sina(self, code: str, start_date: str = None) -> list[dict]:
        """新浪日线 fallback：fund_etf_hist_sina（返回全量历史，按 start_date 过滤）"""
        try:
            symbol = _classify_exchange_symbol(code)
            df = ak.fund_etf_hist_sina(symbol=symbol)
        except Exception as e:
            logger.warning(f"fund_etf_hist_sina({code}) 失败: {e}")
            return []
        if df.empty:
            return []
        results = []
        for _, row in df.iterrows():
            date_str = str(row.get("date", ""))[:10]
            if start_date and date_str < start_date:
                continue
            results.append(
                {
                    "date": date_str,
                    "open": float(row.get("open", 0)),
                    "close": float(row.get("close", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "volume": float(row.get("volume", 0)),
                    "amount": float(row.get("amount", 0) or 0),
                }
            )
        return results

    # ------------------------------------------------------------------
    # 净值：保持原有逻辑（东方财富 fund_etf_fund_info_em 可用）
    # ------------------------------------------------------------------

    def fetch_nav(self, code: str, start_date: str = None) -> list[dict]:
        try:
            df = ak.fund_etf_fund_info_em(fund=code)
        except Exception:
            return []
        if df.empty:
            return []
        results = []
        for _, row in df.iterrows():
            date_str = str(row.get("净值日期", ""))[:10]
            if start_date and date_str < start_date:
                continue
            nav_val = row.get("单位净值", None)
            if pd.notna(nav_val):
                results.append({"date": date_str, "nav": float(nav_val)})
        return results

    def _classify_invest_type(self, name: str) -> str:
        return classify_invest_type(name)

    def _classify_t_plus(self, name: str) -> str:
        return classify_t_plus(name)

    # ------------------------------------------------------------------
    # 分钟线：保持原有逻辑（_em 主源 + _lof fallback）
    # ------------------------------------------------------------------

    def fetch_minute_quotes(
        self, code: str, period: str, start_date: str = None
    ) -> list[dict]:
        """获取指定基金的分钟线行情
        Args:
            code: 基金代码
            period: 周期标识 '1', '5', '60'
            start_date: 开始日期 (YYYY-MM-DD)，可选
        Returns:
            [{"datetime": "YYYY-MM-DD HH:MM:SS", "open": float, "close": float,
              "high": float, "low": float, "volume": float, "amount": float}]
        """
        if period not in ("1", "5", "60"):
            return []

        try:
            df = ak.fund_etf_hist_min_em(symbol=code, period=period)
        except Exception:
            try:
                df = ak.fund_lof_hist_min_em(symbol=code, period=period)
            except Exception:
                return []

        if df.empty:
            return []

        results = []
        for _, row in df.iterrows():
            time_str = str(row.get("时间", ""))
            if " " in time_str:
                datetime_str = time_str[:19]
            else:
                datetime_str = time_str

            # 如果指定了 start_date，进行过滤
            if start_date:
                date_part = datetime_str[:10]
                if date_part < start_date:
                    continue

            results.append(
                {
                    "datetime": datetime_str,
                    "open": float(row.get("开盘", 0)),
                    "close": float(row.get("收盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "volume": float(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                }
            )

        return results
