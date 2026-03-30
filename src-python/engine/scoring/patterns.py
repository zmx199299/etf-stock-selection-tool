import pandas as pd
import numpy as np

class PatternRecognizer:
    def __init__(self):
        pass

    def detect_v_reversal(self, df: pd.DataFrame) -> bool:
        """
        检测 V 型反转：通常指盘中（或近几日）急跌后快速拉升。
        简单实现规则：最后一日收盘价接近当日最高价，且当日最低价远低于开盘价/昨日收盘价。
        """
        if df.empty or len(df) < 2:
            return False
            
        last_day = df.iloc[-1]
        
        # 提取指标
        open_price = last_day['open']
        high_price = last_day['high']
        low_price = last_day['low']
        close_price = last_day['close']
        
        # 实体大小
        body = abs(close_price - open_price)
        # 下影线长度
        lower_shadow = min(open_price, close_price) - low_price
        # 上影线长度
        upper_shadow = high_price - max(open_price, close_price)
        
        # V型反转的条件：
        # 1. 较长的下影线（通常是实体的2倍以上）
        # 2. 几乎没有上影线（收在最高点附近）
        # 3. 最低价相较于昨日收盘或开盘有明显下跌
        
        # 容错处理：若高低价等于开收盘，可能会导致分母为0等问题
        range_val = high_price - low_price
        if range_val == 0:
            return False
            
        # 认为下影线明显大于实体且占全日振幅的大部分，就算日内V反
        # 并且收盘价位于当日前30%的水平
        is_long_lower_shadow = lower_shadow > body * 1.5
        is_close_near_high = (high_price - close_price) / range_val < 0.3
        
        return bool(is_long_lower_shadow and is_close_near_high)

    def detect_all(self, df: pd.DataFrame) -> dict:
        """
        一次性检测所有形态，并返回字典结果。
        """
        return {
            "v_reversal": self.detect_v_reversal(df)
        }
