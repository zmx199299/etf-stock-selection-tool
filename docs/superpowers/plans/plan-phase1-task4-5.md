# 阶段一续：Task 4-5（数据源 + 技术指标）

## Task 4: 数据源抽象接口 + akshare 实现

**Files:**
- Create: `src-python/engine/data/base.py`
- Create: `src-python/engine/data/akshare_source.py`
- Test: `src-python/tests/test_data_source.py`

- [ ] **Step 1: 编写数据源接口测试**

```python
# src-python/tests/test_data_source.py
import pytest
from engine.data.base import DataSource
from engine.data.akshare_source import AkshareSource

def test_akshare_source_implements_interface():
    source = AkshareSource()
    assert isinstance(source, DataSource)

def test_fetch_fund_list():
    """集成测试：需要联网"""
    source = AkshareSource()
    funds = source.fetch_fund_list()
    assert len(funds) > 0
    first = funds[0]
    assert "code" in first
    assert "name" in first
    assert "fund_type" in first

def test_fetch_daily_quotes():
    """集成测试：需要联网，取沪深300ETF近5日数据"""
    source = AkshareSource()
    quotes = source.fetch_daily_quotes("510300", start_date="2026-03-20")
    assert len(quotes) > 0
    first = quotes[0]
    for key in ["date","open","close","high","low","volume","amount"]:
        assert key in first

def test_fetch_nav():
    """集成测试：需要联网"""
    source = AkshareSource()
    nav_data = source.fetch_nav("510300", start_date="2026-03-20")
    assert len(nav_data) > 0
    first = nav_data[0]
    assert "date" in first
    assert "nav" in first
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest src-python/tests/test_data_source.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现抽象接口 base.py**

```python
# src-python/engine/data/base.py
from abc import ABC, abstractmethod

class DataSource(ABC):
    """数据源抽象接口，新数据源只需实现此接口即可接入"""

    @abstractmethod
    def fetch_fund_list(self) -> list[dict]:
        """获取所有场内基金列表
        返回: [{"code","name","fund_type","invest_type","t_plus","list_date","is_excluded"}]
        """
        ...

    @abstractmethod
    def fetch_daily_quotes(self, code: str, start_date: str = None) -> list[dict]:
        """获取指定基金的日线行情
        返回: [{"date","open","close","high","low","volume","amount"}]
        """
        ...

    @abstractmethod
    def fetch_nav(self, code: str, start_date: str = None) -> list[dict]:
        """获取指定基金的净值数据
        返回: [{"date","nav"}]
        """
        ...
```

- [ ] **Step 4: 实现 akshare_source.py**

```python
# src-python/engine/data/akshare_source.py
import akshare as ak
import pandas as pd
from .base import DataSource

# T+0 基金关键词（跨境、货币、债券、黄金、商品类ETF支持T+0）
T0_KEYWORDS = ["跨境", "QDII", "黄金", "商品", "货币", "债券", "油", "铜", "豆粕"]
# 排除关键词
EXCLUDE_KEYWORDS_MONEY = ["货币"]
EXCLUDE_KEYWORDS_BOND = ["债券", "债"]
# 投资类别映射关键词
INVEST_TYPE_MAP = [
    (["跨境", "QDII", "纳指", "标普", "日经", "恒生", "港股"], "跨境型(QDII)"),
    (["黄金", "白银", "油", "铜", "豆粕", "商品"], "商品型"),
    (["REITs", "REIT", "产园", "仓储", "产业园"], "REITs"),
    (["行业", "主题", "科技", "医药", "消费", "军工", "新能源", "半导体", "芯片", "光伏"], "行业主题型"),
    (["沪深300", "中证500", "中证1000", "上证50", "创业板", "指数"], "指数型"),
]

class AkshareSource(DataSource):

    def fetch_fund_list(self) -> list[dict]:
        # 获取ETF列表
        df_etf = ak.fund_etf_spot_em()
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
                    "invest_type": self._classify_invest_type(name),
                    "t_plus": self._classify_t_plus(name),
                    "list_date": "",
                    "is_excluded": 1 if self._is_excluded(name) else 0,
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
        for keywords, itype in INVEST_TYPE_MAP:
            if any(kw in name for kw in keywords):
                return itype
        return "股票型"

    def _classify_t_plus(self, name: str) -> str:
        if any(kw in name for kw in T0_KEYWORDS):
            return "T+0"
        return "T+1"

    def _is_excluded(self, name: str) -> bool:
        for kw in EXCLUDE_KEYWORDS_MONEY:
            if kw in name:
                return True
        for kw in EXCLUDE_KEYWORDS_BOND:
            if kw in name:
                return True
        return False
```

- [ ] **Step 5: 运行测试确认通过**

```bash
python -m pytest src-python/tests/test_data_source.py -v
```
Expected: 4 passed

- [ ] **Step 6: 提交**

```bash
git add src-python/engine/data/ src-python/tests/test_data_source.py
git commit -m "feat: add data source abstraction and akshare implementation"
```

---

## Task 5: 技术指标计算模块

**Files:**
- Create: `src-python/engine/scoring/indicators.py`
- Test: `src-python/tests/test_indicators.py`

- [ ] **Step 1: 编写技术指标测试**

```python
# src-python/tests/test_indicators.py
import pandas as pd
import numpy as np
import pytest
from engine.scoring.indicators import TechnicalIndicators

@pytest.fixture
def sample_df():
    """构造60天的模拟行情数据"""
    np.random.seed(42)
    n = 60
    close = 10 + np.cumsum(np.random.randn(n) * 0.1)
    high = close + np.abs(np.random.randn(n) * 0.05)
    low = close - np.abs(np.random.randn(n) * 0.05)
    opn = close + np.random.randn(n) * 0.02
    volume = np.random.randint(10000, 100000, n).astype(float)
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n),
        "open": opn, "close": close, "high": high, "low": low,
        "volume": volume, "amount": volume * close,
    })

def test_compute_all_returns_dataframe(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(sample_df)

def test_trend_indicators_exist(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    for col in ["ma5","ma10","ma20","ma60","ema12","ema26","macd","macd_signal","macd_hist"]:
        assert col in result.columns, f"Missing {col}"

def test_momentum_indicators_exist(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    for col in ["rsi6","rsi12","rsi24","k","d","j","wr"]:
        assert col in result.columns, f"Missing {col}"

def test_volatility_indicators_exist(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    for col in ["boll_upper","boll_mid","boll_lower","atr14"]:
        assert col in result.columns, f"Missing {col}"

def test_volume_indicators_exist(sample_df):
    ti = TechnicalIndicators()
    result = ti.compute_all(sample_df)
    for col in ["obv","volume_ratio"]:
        assert col in result.columns, f"Missing {col}"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest src-python/tests/test_indicators.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 indicators.py**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest src-python/tests/test_indicators.py -v
```
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/scoring/indicators.py src-python/tests/test_indicators.py
git commit -m "feat: add technical indicators calculation module"
```
