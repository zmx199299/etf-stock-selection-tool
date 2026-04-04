# src-python/engine/services/fund_service.py
"""基金业务逻辑层：查询列表、计算指标、评分、文字化"""
import logging
import pandas as pd
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer

logger = logging.getLogger(__name__)


class FundService:
    def __init__(self, db, indicators: TechnicalIndicators, scorer: Scorer):
        self.db = db
        self.indicators = indicators
        self.scorer = scorer

    def get_fund_list(self) -> list[dict]:
        """获取全量基金列表，包含最新行情、技术指标、评分"""
        funds = self.db.get_all_active_funds()
        if not funds:
            return []

        results = []
        for fund in funds:
            code = fund["code"]
            quotes = self.db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
            if not quotes:
                continue

            df = self._quotes_to_df(quotes)
            df_with_indicators = self.indicators.compute_all(df)

            # 取最新一天的数据
            latest = df_with_indicators.iloc[-1]
            prev = df_with_indicators.iloc[-2] if len(df_with_indicators) > 1 else latest

            # 行情字段
            prev_close = float(prev["close"])
            open_price = float(latest["open"])
            close_price = float(latest["close"])
            high_price = float(latest["high"])
            low_price = float(latest["low"])
            volatility = (high_price - low_price) / low_price if low_price != 0 else 0.0

            # 技术指标文字化
            macd_val = self._describe_macd(latest)
            rsi_val = self._describe_rsi(latest)
            boll_val = self._describe_boll(latest)
            ma5_val = self._describe_ma5(latest, df_with_indicators)
            ma20_val = self._describe_ma20(df_with_indicators)

            # 评分
            score_result = self.scorer.score(df_with_indicators)
            score = max(1, min(10, round(score_result["total_score"] / 10)))

            results.append({
                "code": code,
                "name": fund["name"],
                "prev_close": round(prev_close, 3),
                "open": round(open_price, 3),
                "close": round(close_price, 3),
                "high": round(high_price, 3),
                "low": round(low_price, 3),
                "volatility": round(volatility, 4),
                "macd": macd_val,
                "rsi": rsi_val,
                "boll": boll_val,
                "ma5": ma5_val,
                "ma20": ma20_val,
                "score": score,
            })

        return results

    # --- 技术指标文字化 ---

    def _describe_macd(self, row) -> dict:
        dif = row.get("macd", 0)
        dea = row.get("macd_signal", 0)
        hist = row.get("macd_hist", 0)
        if hist > 0.01:
            return {"value": "红柱", "signal": "bullish"}
        elif hist < -0.01:
            return {"value": "绿柱", "signal": "bearish"}
        else:
            return {"value": "粘合", "signal": "neutral"}

    def _describe_rsi(self, row) -> dict:
        rsi = row.get("rsi12", 50)
        val = str(int(round(rsi))) if not pd.isna(rsi) else "50"
        rsi_num = float(rsi) if not pd.isna(rsi) else 50
        if rsi_num > 60:
            return {"value": val, "signal": "bullish"}
        elif rsi_num < 40:
            return {"value": val, "signal": "bearish"}
        else:
            return {"value": val, "signal": "neutral"}

    def _describe_boll(self, row) -> dict:
        close = row.get("close", 0)
        upper = row.get("boll_upper", 0)
        mid = row.get("boll_mid", 0)
        lower = row.get("boll_lower", 0)
        if pd.isna(upper) or pd.isna(mid) or pd.isna(lower):
            return {"value": "中轨", "signal": "neutral"}
        dist_upper = abs(close - upper)
        dist_mid = abs(close - mid)
        dist_lower = abs(close - lower)
        min_dist = min(dist_upper, dist_mid, dist_lower)
        if min_dist == dist_upper:
            return {"value": "上轨", "signal": "bearish"}
        elif min_dist == dist_lower:
            return {"value": "下轨", "signal": "bullish"}
        else:
            return {"value": "中轨", "signal": "neutral"}

    def _describe_ma5(self, row, df) -> dict:
        ma5 = row.get("ma5", 0)
        ma20 = row.get("ma20", 0)
        if pd.isna(ma5) or pd.isna(ma20):
            return {"value": "粘合", "signal": "neutral"}
        diff_pct = abs(ma5 - ma20) / ma20 if ma20 != 0 else 0
        if diff_pct < 0.005:
            return {"value": "粘合", "signal": "neutral"}
        elif ma5 > ma20:
            return {"value": "多头", "signal": "bullish"}
        else:
            return {"value": "空头", "signal": "bearish"}

    def _describe_ma20(self, df) -> dict:
        if len(df) < 3:
            return {"value": "粘合", "signal": "neutral"}
        ma20_vals = df["ma20"].dropna().tail(3).values
        if len(ma20_vals) < 3:
            return {"value": "粘合", "signal": "neutral"}
        slope = ma20_vals[-1] - ma20_vals[0]
        avg = ma20_vals.mean()
        slope_pct = abs(slope) / avg if avg != 0 else 0
        if slope_pct < 0.002:
            return {"value": "粘合", "signal": "neutral"}
        elif slope > 0:
            return {"value": "向上", "signal": "bullish"}
        else:
            return {"value": "向下", "signal": "bearish"}

    # --- 工具方法 ---

    def _quotes_to_df(self, quotes: list[dict]):
        import pandas as pd
        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values("date").reset_index(drop=True)
