"""分析数据服务：将数据库数据转换为前端 AnalysisPeriod 格式"""
import pandas as pd
from typing import Optional
from engine.models.database import Database
from engine.scoring.indicators import TechnicalIndicators


# 周期标签映射
PERIOD_LABELS = {
    "intraday": "分时",
    "day": "日K",
    "m5": "5分",
    "m60": "60分",
    "m120": "120分",
    "week": "周K",
    "month": "月K",
    "quarter": "季K",
    "year": "年K",
}


class AnalysisService:
    """分析数据服务"""

    def __init__(self, db: Database, indicators: TechnicalIndicators):
        self.db = db
        self.indicators = indicators

    def get_analysis_data(self, code: str) -> Optional[dict]:
        """获取指定基金的完整分析数据"""
        fund = self.db.get_fund_info(code)
        if not fund:
            return None

        # 获取最新日线数据用于基础信息
        quotes = self.db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
        if not quotes:
            return None

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        current_price = float(latest["close"])
        prev_close = float(prev["close"])
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close != 0 else 0.0

        nav = float(latest.get("nav", 0)) if pd.notna(latest.get("nav")) else None
        premium_rate = float(latest.get("premium_rate", 0)) * 100 if pd.notna(latest.get("premium_rate")) else None

        return {
            "code": code,
            "name": fund["name"],
            "market": "SH" if code.startswith(("51", "58", "56")) else "SZ",
            "price": f"{current_price:.3f}",
            "change": f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%",
            "iopv": f"{nav:.3f}" if nav else "N/A",
            "premium": f"{'+' if premium_rate and premium_rate >= 0 else ''}{premium_rate:.2f}%" if premium_rate is not None else "N/A",
            "riskLevel": self._estimate_risk_level(df),
            "strategy": self._generate_strategy(df),
            "periods": {
                "intraday": self.get_intraday_period(code),
                "day": self.get_day_period(code),
                "m5": self.get_minute_period(code, "m5", "5"),
                "m60": self.get_minute_period(code, "m60", "60"),
                "m120": self.get_minute_period(code, "m120", "120"),
                "week": self.get_aggregated_period(code, "week"),
                "month": self.get_aggregated_period(code, "month"),
                "quarter": self.get_aggregated_period(code, "quarter"),
                "year": self.get_aggregated_period(code, "year"),
            },
        }

    def get_day_period(self, code: str) -> dict:
        """获取日线周期数据"""
        quotes = self.db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
        if not quotes:
            return self._empty_period("day")

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        # 取最近 60 条
        df = df.tail(60)

        candles = df[["open", "high", "low", "close"]].values.tolist()
        volumes = df["volume"].tolist()
        time_axis = [d[-5:] for d in df["date"].tolist()]  # MM-DD
        price_axis = self._calc_price_axis(df)
        metrics = self._calc_metrics(df)

        return {
            "key": "day",
            "label": PERIOD_LABELS["day"],
            "summary": f"日线数据显示最近 {len(df)} 个交易日走势",
            "chartHeadline": f"日线趋势观察",
            "chartSummary": f"基于 {len(df)} 个交易日的数据分析",
            "priceAxis": price_axis,
            "timeAxis": time_axis,
            "linePoints": df["close"].tolist(),
            "avgLinePoints": df["close"].rolling(5).mean().bfill().tolist(),
            "candles": candles,
            "volumes": volumes,
            "metrics": metrics,
        }

    def get_minute_period(self, code: str, key: str, period: str) -> dict:
        """获取分钟线周期数据"""
        quotes = self.db.get_minute_quotes(code, period, "2000-01-01 00:00:00", "2099-12-31 23:59:59")
        if not quotes:
            return self._empty_period(key)

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("datetime").reset_index(drop=True)

        # 取最近 120 条
        df = df.tail(120)

        candles = df[["open", "high", "low", "close"]].values.tolist()
        volumes = df["volume"].tolist()
        time_axis = [d[11:16] for d in df["datetime"].tolist()]  # HH:MM
        price_axis = self._calc_price_axis(df)
        metrics = self._calc_metrics(df)

        return {
            "key": key,
            "label": PERIOD_LABELS[key],
            "summary": f"{PERIOD_LABELS[key]}数据显示最近 {len(df)} 根K线走势",
            "chartHeadline": f"{PERIOD_LABELS[key]}趋势观察",
            "chartSummary": f"基于 {len(df)} 根K线的数据分析",
            "priceAxis": price_axis,
            "timeAxis": time_axis,
            "linePoints": df["close"].tolist(),
            "avgLinePoints": df["close"].rolling(5).mean().bfill().tolist(),
            "candles": candles,
            "volumes": volumes,
            "metrics": metrics,
        }

    def get_intraday_period(self, code: str) -> dict:
        """获取分时数据（当日 1 分钟线）"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        start = f"{today} 00:00:00"
        end = f"{today} 23:59:59"

        quotes = self.db.get_minute_quotes(code, "1", start, end)
        if not quotes:
            return self._empty_period("intraday")

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("datetime").reset_index(drop=True)

        line_points = df["close"].tolist()
        # 均价线 = 累计成交额 / 累计成交量
        df["cum_amount"] = df["amount"].cumsum()
        df["cum_volume"] = df["volume"].cumsum()
        avg_line_points = (df["cum_amount"] / df["cum_volume"].replace(0, float("nan"))).ffill().tolist()

        time_axis = [d[11:16] for d in df["datetime"].tolist()]
        price_axis = self._calc_price_axis(df)

        return {
            "key": "intraday",
            "label": PERIOD_LABELS["intraday"],
            "summary": f"分时数据显示当日 {len(df)} 个分钟走势",
            "chartHeadline": "分时价格走势",
            "chartSummary": f"基于当日 {len(df)} 根 1 分钟K线",
            "priceAxis": price_axis,
            "timeAxis": time_axis,
            "linePoints": line_points,
            "avgLinePoints": avg_line_points,
            "candles": [],  # 分时图不使用 K 线
            "volumes": df["volume"].tolist(),
            "metrics": self._calc_intraday_metrics(df),
        }

    def get_aggregated_period(self, code: str, key: str) -> dict:
        """获取聚合周期数据（周/月/季/年）"""
        quotes = self.db.get_daily_quotes(code, "2000-01-01", "2099-12-31")
        if not quotes:
            return self._empty_period(key)

        df = pd.DataFrame(quotes)
        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

        # 按周期聚合
        df["date"] = pd.to_datetime(df["date"])
        if key == "week":
            df["period_key"] = df["date"].dt.to_period("W")
        elif key == "month":
            df["period_key"] = df["date"].dt.to_period("M")
        elif key == "quarter":
            df["period_key"] = df["date"].dt.to_period("Q")
        elif key == "year":
            df["period_key"] = df["date"].dt.to_period("Y")
        else:
            return self._empty_period(key)

        agg_df = df.groupby("period_key").agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            amount=("amount", "sum"),
        ).reset_index()

        # 取最近 60 条
        agg_df = agg_df.tail(60)

        candles = agg_df[["open", "high", "low", "close"]].values.tolist()
        volumes = agg_df["volume"].tolist()

        if key == "week":
            time_axis = [f"第{i+1}周" for i in range(len(agg_df))]
        elif key == "month":
            time_axis = [str(p)[:7] for p in agg_df["period_key"]]
        elif key == "quarter":
            time_axis = [f"Q{p.quarter}" for p in agg_df["period_key"]]
        elif key == "year":
            time_axis = [str(p.year) for p in agg_df["period_key"]]
        else:
            time_axis = []

        price_axis = self._calc_price_axis(agg_df)
        metrics = self._calc_metrics(agg_df)

        return {
            "key": key,
            "label": PERIOD_LABELS[key],
            "summary": f"{PERIOD_LABELS[key]}数据显示最近 {len(agg_df)} 个周期走势",
            "chartHeadline": f"{PERIOD_LABELS[key]}趋势观察",
            "chartSummary": f"基于 {len(agg_df)} 个{PERIOD_LABELS[key]}的数据分析",
            "priceAxis": price_axis,
            "timeAxis": time_axis,
            "linePoints": agg_df["close"].tolist(),
            "avgLinePoints": agg_df["close"].rolling(5).mean().bfill().tolist(),
            "candles": candles,
            "volumes": volumes,
            "metrics": metrics,
        }

    def _empty_period(self, key: str) -> dict:
        """返回空周期数据"""
        return {
            "key": key,
            "label": PERIOD_LABELS.get(key, key),
            "summary": "暂无数据",
            "chartHeadline": "数据加载中",
            "chartSummary": "该周期暂无可用数据",
            "priceAxis": [],
            "timeAxis": [],
            "linePoints": [],
            "avgLinePoints": [],
            "candles": [],
            "volumes": [],
            "metrics": [],
        }

    def _calc_price_axis(self, df: pd.DataFrame) -> list[str]:
        """计算价格轴刻度"""
        if df.empty:
            return []
        min_val = df[["low", "open", "close"]].min().min()
        max_val = df[["high", "open", "close"]].max().max()
        if min_val == max_val:
            min_val -= 0.01
            max_val += 0.01
        step = (max_val - min_val) / 4
        return [f"{min_val + i * step:.2f}" for i in range(5)]

    def _calc_metrics(self, df: pd.DataFrame) -> list[dict]:
        """计算技术指标"""
        if len(df) < 20:
            return [{"label": "数据不足", "value": "N/A", "summary": "数据量不足以计算指标", "tone": "neutral"}]

        df_copy = df.copy()
        df_copy = self.indicators.compute_all(df_copy)

        latest = df_copy.iloc[-1]
        metrics = []

        # MACD
        if pd.notna(latest.get("macd_hist")):
            macd_val = latest["macd_hist"]
            if macd_val > 0:
                metrics.append({"label": "MACD", "value": "金叉", "summary": "短线动能转强", "tone": "bullish"})
            elif macd_val < 0:
                metrics.append({"label": "MACD", "value": "死叉", "summary": "短线动能转弱", "tone": "bearish"})
            else:
                metrics.append({"label": "MACD", "value": "粘合", "summary": "多空平衡", "tone": "neutral"})

        # RSI
        if pd.notna(latest.get("rsi6")):
            rsi = latest["rsi6"]
            if rsi > 70:
                metrics.append({"label": "RSI", "value": f"{rsi:.0f}", "summary": "接近超买区域", "tone": "bearish"})
            elif rsi < 30:
                metrics.append({"label": "RSI", "value": f"{rsi:.0f}", "summary": "接近超卖区域", "tone": "bullish"})
            else:
                metrics.append({"label": "RSI", "value": f"{rsi:.0f}", "summary": "中性区域", "tone": "neutral"})

        # BOLL
        if pd.notna(latest.get("boll_mid")):
            close = latest["close"]
            if close > latest["boll_upper"]:
                metrics.append({"label": "BOLL", "value": "突破上轨", "summary": "价格强势突破", "tone": "bullish"})
            elif close < latest["boll_lower"]:
                metrics.append({"label": "BOLL", "value": "跌破下轨", "summary": "价格弱势突破", "tone": "bearish"})
            else:
                metrics.append({"label": "BOLL", "value": "通道内", "summary": "价格在通道内运行", "tone": "neutral"})

        # 均线
        if pd.notna(latest.get("ma5")) and pd.notna(latest.get("ma20")):
            if latest["ma5"] > latest["ma20"]:
                metrics.append({"label": "均线", "value": "多头排列", "summary": "短期趋势向上", "tone": "bullish"})
            else:
                metrics.append({"label": "均线", "value": "空头排列", "summary": "短期趋势向下", "tone": "bearish"})

        return metrics if metrics else [{"label": "指标", "value": "N/A", "summary": "暂无信号", "tone": "neutral"}]

    def _calc_intraday_metrics(self, df: pd.DataFrame) -> list[dict]:
        """计算分时指标"""
        if df.empty:
            return []

        latest = df.iloc[-1]
        first = df.iloc[0]
        change = (latest["close"] - first["open"]) / first["open"] * 100 if first["open"] != 0 else 0

        metrics = []
        if change > 0.5:
            metrics.append({"label": "分时强度", "value": "偏强", "summary": f"当日涨幅 {change:.2f}%", "tone": "bullish"})
        elif change < -0.5:
            metrics.append({"label": "分时强度", "value": "偏弱", "summary": f"当日跌幅 {abs(change):.2f}%", "tone": "bearish"})
        else:
            metrics.append({"label": "分时强度", "value": "平稳", "summary": f"当日波动 {abs(change):.2f}%", "tone": "neutral"})

        return metrics

    def _estimate_risk_level(self, df: pd.DataFrame) -> str:
        """估算风险等级"""
        if len(df) < 20:
            return "数据不足"

        df_copy = df.copy()
        df_copy = self.indicators.compute_all(df_copy)
        atr = df_copy.iloc[-1].get("atr14", 0)
        if pd.isna(atr):
            return "中等波动"

        close = df_copy.iloc[-1]["close"]
        atr_pct = atr / close * 100 if close > 0 else 0

        if atr_pct < 1:
            return "低波动"
        elif atr_pct < 2:
            return "中等波动"
        elif atr_pct < 3:
            return "中高波动"
        else:
            return "高波动"

    def _generate_strategy(self, df: pd.DataFrame) -> dict:
        """生成策略建议"""
        if len(df) < 20:
            return {
                "conclusion": "数据不足，暂无法生成策略",
                "buyZone": "N/A",
                "sellZone": "N/A",
                "position": "观望",
                "stopLoss": "N/A",
                "holdingPeriod": "N/A",
                "riskNote": "数据量不足，建议等待更多数据积累",
            }

        df_copy = df.copy()
        df_copy = self.indicators.compute_all(df_copy)
        latest = df_copy.iloc[-1]

        # 简单策略逻辑
        bullish_signals = 0
        if pd.notna(latest.get("macd_hist")) and latest["macd_hist"] > 0:
            bullish_signals += 1
        if pd.notna(latest.get("rsi6")) and 30 < latest["rsi6"] < 70:
            bullish_signals += 1
        if pd.notna(latest.get("ma5")) and pd.notna(latest.get("ma20")) and latest["ma5"] > latest["ma20"]:
            bullish_signals += 1

        current_price = latest["close"]

        if bullish_signals >= 2:
            conclusion = "趋势偏多，可关注回踩机会"
            position = "建议 3-5 成仓位"
            buy_zone = f"{current_price * 0.98:.2f} - {current_price * 0.99:.2f}"
            sell_zone = f"{current_price * 1.03:.2f} - {current_price * 1.05:.2f}"
            stop_loss = f"{current_price * 0.96:.2f}"
        elif bullish_signals == 1:
            conclusion = "多空平衡，等待方向确认"
            position = "建议 1-3 成试探仓位"
            buy_zone = f"{current_price * 0.97:.2f} - {current_price * 0.98:.2f}"
            sell_zone = f"{current_price * 1.02:.2f} - {current_price * 1.04:.2f}"
            stop_loss = f"{current_price * 0.95:.2f}"
        else:
            conclusion = "趋势偏空，建议观望"
            position = "建议空仓或极轻仓位"
            buy_zone = f"{current_price * 0.95:.2f} - {current_price * 0.97:.2f}"
            sell_zone = f"{current_price * 1.01:.2f} - {current_price * 1.03:.2f}"
            stop_loss = f"{current_price * 0.93:.2f}"

        return {
            "conclusion": conclusion,
            "buyZone": buy_zone,
            "sellZone": sell_zone,
            "position": position,
            "stopLoss": f"跌破 {stop_loss} 止损",
            "holdingPeriod": "3-10 个交易日",
            "riskNote": "以上为系统自动分析，仅供参考",
        }
