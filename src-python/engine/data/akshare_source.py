# src-python/engine/data/akshare_source.py
import akshare as ak
import pandas as pd
from .base import DataSource

# T+0 基金关键词（跨境、货币、债券、黄金、商品类ETF支持T+0）
T0_KEYWORDS = ["跨境", "QDII", "黄金", "商品", "货币", "债券", "油", "铜", "豆粕", "标普", "纳指", "恒生", "日经", "港股"]
# 排除关键词
EXCLUDE_KEYWORDS_MONEY = ["货币", "理财", "现金"]
EXCLUDE_KEYWORDS_BOND = ["债券", "债", "利率", "城投"]
# 投资类别映射关键词
INVEST_TYPE_MAP = [
    (["跨境", "QDII", "纳指", "标普", "日经", "恒生", "港股", "德国", "法国"], "跨境型(QDII)"),
    (["黄金", "白银", "油", "铜", "豆粕", "商品", "有色"], "商品型"),
    (["REITs", "REIT", "产园", "仓储", "产业园", "高速", "保障房"], "REITs"),
    (["行业", "主题", "科技", "医药", "消费", "军工", "新能源", "半导体", "芯片", "光伏", "白酒", "金融", "银行", "地产", "煤炭", "钢铁", "农业"], "行业主题型"),
    (["沪深300", "中证500", "中证1000", "上证50", "创业板", "科创", "指数", "红利"], "指数型"),
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


class AkshareSource(DataSource):

    def fetch_fund_list(self) -> list[dict]:
        # 获取ETF列表
        try:
            df_etf = ak.fund_etf_spot_em()
        except Exception:
            df_etf = pd.DataFrame()
            
        # 获取LOF列表
        try:
            df_lof = ak.fund_lof_spot_em()
        except Exception:
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

    def fetch_daily_quotes(self, code: str, start_date: str = None) -> list[dict]:
        try:
            df = ak.fund_etf_hist_em(
                symbol=code, period="daily",
                start_date=start_date.replace("-", "") if start_date else "19900101",
                adjust=""
            )
        except Exception:
            return []
        if df.empty:
            return []
        results = []
        for _, row in df.iterrows():
            results.append({
                "date": str(row.get("日期", ""))[:10],
                "open": float(row.get("开盘", 0)),
                "close": float(row.get("收盘", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
            })
        return results

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
            if nav_val is not None:
                results.append({"date": date_str, "nav": float(nav_val)})
        return results

    def _classify_invest_type(self, name: str) -> str:
        return classify_invest_type(name)

    def _classify_t_plus(self, name: str) -> str:
        return classify_t_plus(name)
