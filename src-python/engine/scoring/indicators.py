# src-python/engine/scoring/indicators.py
import pandas as pd
import numpy as np

class TechnicalIndicators:
    """技术指标计算，所有指标从本地 DataFrame 计算，不联网"""

    def compute_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算全部技术指标，返回带指标列的 DataFrame"""
        result = df.copy()
        self._add_trend(result)
        self._add_momentum(result)
        self._add_volatility(result)
        self._add_volume(result)
        return result

    def _add_trend(self, df: pd.DataFrame):
        c = df["close"]
        df["ma5"] = c.rolling(5).mean()
        df["ma10"] = c.rolling(10).mean()
        df["ma20"] = c.rolling(20).mean()
        df["ma60"] = c.rolling(60).mean()
        df["ema12"] = c.ewm(span=12, adjust=False).mean()
        df["ema26"] = c.ewm(span=26, adjust=False).mean()
        dif = df["ema12"] - df["ema26"]
        dea = dif.ewm(span=9, adjust=False).mean()
        df["macd"] = dif
        df["macd_signal"] = dea
        df["macd_hist"] = 2 * (dif - dea)

    def _add_momentum(self, df: pd.DataFrame):
        c = df["close"]
        for period in [6, 12, 24]:
            delta = c.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(period).mean()
            avg_loss = loss.rolling(period).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            df[f"rsi{period}"] = 100 - 100 / (1 + rs)

        # KDJ
        low_min = df["low"].rolling(9).min()
        high_max = df["high"].rolling(9).max()
        rsv = (c - low_min) / (high_max - low_min).replace(0, np.nan) * 100
        df["k"] = rsv.ewm(com=2, adjust=False).mean()
        df["d"] = df["k"].ewm(com=2, adjust=False).mean()
        df["j"] = 3 * df["k"] - 2 * df["d"]

        # WR (Williams %R, 14期)
        h14 = df["high"].rolling(14).max()
        l14 = df["low"].rolling(14).min()
        df["wr"] = (h14 - c) / (h14 - l14).replace(0, np.nan) * -100

    def _add_volatility(self, df: pd.DataFrame):
        c = df["close"]
        # Bollinger Bands (20, 2)
        df["boll_mid"] = c.rolling(20).mean()
        std = c.rolling(20).std()
        df["boll_upper"] = df["boll_mid"] + 2 * std
        df["boll_lower"] = df["boll_mid"] - 2 * std

        # ATR (14)
        h = df["high"]
        l = df["low"]
        prev_c = c.shift(1)
        tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
        df["atr14"] = tr.rolling(14).mean()

    def _add_volume(self, df: pd.DataFrame):
        # OBV
        direction = np.sign(df["close"].diff())
        df["obv"] = (direction * df["volume"]).cumsum()

        # 量比 = 当日成交量 / 过去5日均量
        avg5 = df["volume"].rolling(5).mean()
        df["volume_ratio"] = df["volume"] / avg5.replace(0, np.nan)
