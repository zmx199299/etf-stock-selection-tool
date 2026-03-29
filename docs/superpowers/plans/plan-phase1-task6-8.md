# 阶段一续：Task 6-8（评分 + 筛选 + 交易成本）

## Task 6: 综合评分模块

**Files:**
- Create: `src-python/engine/scoring/scorer.py`
- Test: `src-python/tests/test_scorer.py`

- [ ] **Step 1: 编写评分测试**

```python
# src-python/tests/test_scorer.py
import pandas as pd
import numpy as np
import pytest
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer

@pytest.fixture
def sample_indicators():
    np.random.seed(42)
    n = 60
    close = 10 + np.cumsum(np.random.randn(n) * 0.1)
    high = close + np.abs(np.random.randn(n) * 0.05)
    low = close - np.abs(np.random.randn(n) * 0.05)
    opn = close + np.random.randn(n) * 0.02
    volume = np.random.randint(10000, 100000, n).astype(float)
    df = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n),
        "open": opn, "close": close, "high": high, "low": low,
        "volume": volume, "amount": volume * close,
    })
    ti = TechnicalIndicators()
    return ti.compute_all(df)

def test_score_returns_dict(sample_indicators):
    scorer = Scorer()
    result = scorer.score(sample_indicators)
    assert "total_score" in result
    assert "trend_score" in result
    assert "momentum_score" in result
    assert "volatility_score" in result
    assert "volume_score" in result
    assert "signal" in result

def test_score_range(sample_indicators):
    scorer = Scorer()
    result = scorer.score(sample_indicators)
    assert 0 <= result["total_score"] <= 100
    assert 0 <= result["trend_score"] <= 100
    assert result["signal"] in ["强烈看多","看多","中性","看空","强烈看空"]

def test_custom_weights(sample_indicators):
    weights = {"trend": 0.5, "momentum": 0.2, "volatility": 0.1, "volume": 0.2}
    scorer = Scorer(weights=weights)
    result = scorer.score(sample_indicators)
    assert 0 <= result["total_score"] <= 100

def test_buy_value_score(sample_indicators):
    scorer = Scorer()
    last = sample_indicators.iloc[-1]
    result = scorer.buy_value_score(
        tech_score=65, premium_rate=-0.02,
        reversal_strength=0.7, consecutive_days=3,
        volume_ratio=1.5
    )
    assert 0 <= result <= 100
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 scorer.py**

```python
# src-python/engine/scoring/scorer.py
import numpy as np

DEFAULT_WEIGHTS = {"trend": 0.30, "momentum": 0.25, "volatility": 0.20, "volume": 0.25}
DEFAULT_BUY_WEIGHTS = {
    "tech": 0.40, "premium": 0.20, "reversal": 0.15,
    "consecutive": 0.10, "volume_change": 0.15
}
SIGNAL_MAP = [
    (80, "强烈看多"), (60, "看多"), (40, "中性"), (20, "看空"), (0, "强烈看空")
]

class Scorer:
    def __init__(self, weights: dict = None, buy_weights: dict = None):
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.buy_weights = buy_weights or DEFAULT_BUY_WEIGHTS.copy()

    def score(self, df) -> dict:
        """对含技术指标的 DataFrame 计算综合评分，取最后一行的状态"""
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        trend = self._score_trend(last, prev)
        momentum = self._score_momentum(last)
        volatility = self._score_volatility(last)
        volume = self._score_volume(last)

        w = self.weights
        total = (trend * w["trend"] + momentum * w["momentum"]
                 + volatility * w["volatility"] + volume * w["volume"])
        total = np.clip(total, 0, 100)

        return {
            "total_score": round(float(total), 2),
            "trend_score": round(float(trend), 2),
            "momentum_score": round(float(momentum), 2),
            "volatility_score": round(float(volatility), 2),
            "volume_score": round(float(volume), 2),
            "signal": self._to_signal(total),
        }

    def buy_value_score(self, tech_score: float, premium_rate: float,
                        reversal_strength: float, consecutive_days: int,
                        volume_ratio: float) -> float:
        """次日买入价值评分"""
        w = self.buy_weights
        # 折溢价得分：折价越多越高分，高溢价扣分
        premium_score = np.clip(50 - premium_rate * 1000, 0, 100)
        # 反转强度得分：0~1 映射到 0~100
        reversal_score = np.clip(reversal_strength * 100, 0, 100)
        # 连续天数加成：3天=60, 4天=80, 5天+=100
        consec_score = np.clip(consecutive_days * 20, 0, 100)
        # 量变得分：量比 1.5 左右最优
        vol_score = np.clip(volume_ratio * 40, 0, 100)

        total = (tech_score * w["tech"] + premium_score * w["premium"]
                 + reversal_score * w["reversal"] + consec_score * w["consecutive"]
                 + vol_score * w["volume_change"])
        return round(float(np.clip(total, 0, 100)), 2)

    def _score_trend(self, last, prev) -> float:
        score = 50.0
        # MA多头排列加分
        mas = [last.get("ma5"), last.get("ma10"), last.get("ma20")]
        mas = [m for m in mas if m is not None and not np.isnan(m)]
        if len(mas) == 3 and mas[0] > mas[1] > mas[2]:
            score += 20
        elif len(mas) == 3 and mas[0] < mas[1] < mas[2]:
            score -= 20
        # MACD 金叉/死叉
        macd = last.get("macd_hist")
        prev_macd = prev.get("macd_hist")
        if macd is not None and prev_macd is not None:
            if not np.isnan(macd) and not np.isnan(prev_macd):
                if macd > 0 and prev_macd <= 0:
                    score += 15
                elif macd < 0 and prev_macd >= 0:
                    score -= 15
                elif macd > prev_macd:
                    score += 5
                elif macd < prev_macd:
                    score -= 5
        return np.clip(score, 0, 100)

    def _score_momentum(self, last) -> float:
        score = 50.0
        rsi = last.get("rsi12")
        if rsi is not None and not np.isnan(rsi):
            if rsi < 30: score += 25
            elif rsi < 40: score += 10
            elif rsi > 70: score -= 25
            elif rsi > 60: score -= 10
        j = last.get("j")
        if j is not None and not np.isnan(j):
            if j < 0: score += 15
            elif j > 100: score -= 15
        return np.clip(score, 0, 100)

    def _score_volatility(self, last) -> float:
        score = 50.0
        close = last.get("close")
        lower = last.get("boll_lower")
        upper = last.get("boll_upper")
        if all(v is not None and not np.isnan(v) for v in [close, lower, upper]):
            if close <= lower: score += 25
            elif close >= upper: score -= 25
            else:
                mid = (upper + lower) / 2
                if close < mid: score += 10
                else: score -= 10
        return np.clip(score, 0, 100)

    def _score_volume(self, last) -> float:
        score = 50.0
        vr = last.get("volume_ratio")
        if vr is not None and not np.isnan(vr):
            if vr > 2.0: score += 20
            elif vr > 1.5: score += 10
            elif vr < 0.5: score -= 15
        return np.clip(score, 0, 100)

    def _to_signal(self, score: float) -> str:
        for threshold, label in SIGNAL_MAP:
            if score >= threshold:
                return label
        return "强烈看空"
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest src-python/tests/test_scorer.py -v
```
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/scoring/scorer.py src-python/tests/test_scorer.py
git commit -m "feat: add scoring module with tech score and buy value score"
```

---

## Task 7: 日内形态筛选模块

**Files:**
- Create: `src-python/engine/screener/pattern.py`
- Test: `src-python/tests/test_screener.py`

- [ ] **Step 1: 编写筛选测试**

```python
# src-python/tests/test_screener.py
import pytest
from engine.screener.pattern import PatternScreener

@pytest.fixture
def screener():
    return PatternScreener()

@pytest.fixture
def passing_quotes():
    """构造连续3天满足V型反转条件的数据"""
    base = 10.0
    days = []
    for i in range(5):
        prev_close = base + i * 0.01
        low = prev_close * 0.985     # 跌1.5%
        high = low + prev_close * 0.04  # 振幅4%
        close = high - 0.01
        days.append({
            "date": f"2026-03-{24+i:02d}", "code": "510300",
            "open": prev_close, "close": close, "high": high, "low": low,
            "volume": 100000, "amount": 1000000,
            "prev_close": prev_close, "is_suspended": 0,
            "nav": close * 0.99, "premium_rate": 0.01,
        })
    return days

def test_check_single_day_pass(screener, passing_quotes):
    q = passing_quotes[0]
    assert screener.check_single_day(q) is True

def test_check_single_day_fail_amplitude():
    screener = PatternScreener()
    q = {
        "prev_close": 10.0, "high": 10.1, "low": 10.0,
        "close": 10.05, "volume": 100000, "is_suspended": 0,
    }
    assert screener.check_single_day(q) is False  # 振幅只有1%

def test_check_consecutive(screener, passing_quotes):
    result = screener.check_consecutive(passing_quotes, n=3)
    assert result["passed"] is True
    assert result["consecutive_days"] >= 3

def test_suspended_excluded(screener):
    q = {
        "date": "2026-03-28", "prev_close": 10.0,
        "high": 10.4, "low": 9.85, "close": 10.3,
        "volume": 0, "is_suspended": 1,
    }
    assert screener.check_single_day(q) is False
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 pattern.py**

```python
# src-python/engine/screener/pattern.py

DEFAULT_PARAMS = {
    "amplitude_min": 0.035,
    "amplitude_max": 0.045,
    "min_drop": -0.01,
    "consecutive_days": 3,
}

class PatternScreener:
    def __init__(self, params: dict = None):
        self.params = params or DEFAULT_PARAMS.copy()

    def check_single_day(self, q: dict) -> bool:
        """检查单日是否满足V型反转形态条件"""
        prev_close = q.get("prev_close", 0)
        if prev_close <= 0:
            return False
        if q.get("is_suspended", 0):
            return False
        if q.get("volume", 0) <= 0:
            return False

        high = q["high"]
        low = q["low"]

        # ① 振幅
        amplitude = (high - low) / prev_close
        if not (self.params["amplitude_min"] <= amplitude <= self.params["amplitude_max"]):
            return False

        # ② 先跌
        drop = (low - prev_close) / prev_close
        if drop > self.params["min_drop"]:
            return False

        # ③ V型反转
        if high <= low:
            return False

        return True

    def check_consecutive(self, quotes: list[dict], n: int = None) -> dict:
        """检查连续N天是否满足条件"""
        n = n or self.params["consecutive_days"]
        if len(quotes) < n:
            return {"passed": False, "consecutive_days": 0}

        # 从最近的数据往前检查
        count = 0
        for q in reversed(quotes):
            if self.check_single_day(q):
                count += 1
            else:
                break

        return {
            "passed": count >= n,
            "consecutive_days": count,
        }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest src-python/tests/test_screener.py -v
```
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/screener/ src-python/tests/test_screener.py
git commit -m "feat: add intraday V-shape pattern screener"
```

---

## Task 8: 交易成本与资金分配模块

**Files:**
- Create: `src-python/engine/scoring/cost.py`
- Test: `src-python/tests/test_cost.py`

- [ ] **Step 1: 编写交易成本测试**

```python
# src-python/tests/test_cost.py
import pytest
from engine.scoring.cost import CostCalculator

@pytest.fixture
def calc_no_free5():
    return CostCalculator(commission_rate=0.00025, free5=False, min_commission=5, transfer_fee=0.00001)

@pytest.fixture
def calc_free5():
    return CostCalculator(commission_rate=0.00025, free5=True, min_commission=5, transfer_fee=0.00001)

def test_buy_shares_100_multiple(calc_no_free5):
    result = calc_no_free5.compute_buy(price=1.5, budget=3000)
    assert result["shares"] % 100 == 0
    assert result["shares"] > 0

def test_buy_cost_includes_commission(calc_no_free5):
    result = calc_no_free5.compute_buy(price=1.5, budget=3000)
    assert result["commission"] == 5  # 3000*0.025%=0.75 < 5, 触发最低佣金
    assert result["total_cost"] == result["shares"] * 1.5 + result["commission"]

def test_free5_no_min(calc_free5):
    result = calc_free5.compute_buy(price=1.5, budget=3000)
    expected_comm = result["shares"] * 1.5 * 0.00025
    assert abs(result["commission"] - expected_comm) < 0.01

def test_profit_loss_estimation(calc_no_free5):
    buy = calc_no_free5.compute_buy(price=1.5, budget=20000)
    result = calc_no_free5.compute_profit_loss(
        shares=buy["shares"], buy_price=1.5, sell_price=1.56
    )
    assert result["profit"] > 0
    assert result["fee_total"] > 0
    assert result["fee_ratio"] > 0

def test_warning_level_red(calc_no_free5):
    buy = calc_no_free5.compute_buy(price=1.5, budget=1000)
    result = calc_no_free5.compute_profit_loss(
        shares=buy["shares"], buy_price=1.5, sell_price=1.51
    )
    # 小本金 + 不免5 + 小涨幅 → 手续费占比高
    assert result["warning"] in ["red", "orange"]

def test_allocate_equal(calc_no_free5):
    funds = [
        {"code": "510300", "buy_price": 4.0},
        {"code": "159915", "buy_price": 2.0},
    ]
    result = calc_no_free5.allocate(total_budget=20000, funds=funds, mode="equal")
    assert len(result) == 2
    assert sum(r["budget"] for r in result) <= 20000

def test_allocate_over_budget(calc_no_free5):
    funds = [{"code": "510300", "buy_price": 4.0}]
    result = calc_no_free5.allocate(total_budget=100, funds=funds, mode="equal")
    assert result[0]["shares"] == 0  # 资金不足买100份

def test_budget_insufficient(calc_no_free5):
    result = calc_no_free5.compute_buy(price=50.0, budget=100)
    assert result["shares"] == 0
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 cost.py**

```python
# src-python/engine/scoring/cost.py
import math

WARNING_THRESHOLDS = {"red": 0.50, "orange": 0.30}

class CostCalculator:
    def __init__(self, commission_rate: float = 0.00025, free5: bool = False,
                 min_commission: float = 5.0, transfer_fee: float = 0.00001):
        self.commission_rate = commission_rate
        self.free5 = free5
        self.min_commission = min_commission
        self.transfer_fee = transfer_fee

    def _calc_commission(self, amount: float) -> float:
        comm = amount * self.commission_rate
        if not self.free5:
            comm = max(comm, self.min_commission)
        return round(comm, 2)

    def compute_buy(self, price: float, budget: float) -> dict:
        """根据预算和价格计算可买份数与实际成本"""
        if price <= 0 or budget <= 0:
            return {"shares": 0, "commission": 0, "total_cost": 0, "budget": budget}

        # 预估佣金后计算可用金额
        est_commission = self._calc_commission(budget)
        available = budget - est_commission
        if available <= 0:
            return {"shares": 0, "commission": 0, "total_cost": 0, "budget": budget}

        shares = math.floor(available / price / 100) * 100
        if shares <= 0:
            return {"shares": 0, "commission": 0, "total_cost": 0, "budget": budget}

        actual_amount = shares * price
        commission = self._calc_commission(actual_amount)
        total_cost = actual_amount + commission

        return {
            "shares": shares,
            "commission": round(commission, 2),
            "total_cost": round(total_cost, 2),
            "budget": budget,
        }

    def compute_profit_loss(self, shares: int, buy_price: float, sell_price: float) -> dict:
        """计算盈亏预估（含手续费）"""
        buy_amount = shares * buy_price
        buy_comm = self._calc_commission(buy_amount)
        buy_cost = buy_amount + buy_comm

        sell_amount = shares * sell_price
        sell_comm = self._calc_commission(sell_amount)
        sell_transfer = round(sell_amount * self.transfer_fee, 2)
        sell_income = sell_amount - sell_comm - sell_transfer

        profit = round(sell_income - buy_cost, 2)
        profit_rate = round(profit / buy_cost, 6) if buy_cost > 0 else 0
        fee_total = round(buy_comm + sell_comm + sell_transfer, 2)
        fee_ratio = round(fee_total / profit, 4) if profit > 0 else 999

        # 预警级别
        if profit <= 0:
            warning = "red"
        elif fee_ratio > WARNING_THRESHOLDS["red"]:
            warning = "red"
        elif fee_ratio > WARNING_THRESHOLDS["orange"]:
            warning = "orange"
        elif not self.free5 and (buy_comm == self.min_commission or sell_comm == self.min_commission):
            warning = "yellow"
        else:
            warning = "green"

        return {
            "profit": profit,
            "profit_rate": profit_rate,
            "fee_total": fee_total,
            "fee_ratio": fee_ratio,
            "warning": warning,
            "buy_commission": buy_comm,
            "sell_commission": sell_comm,
            "sell_transfer_fee": sell_transfer,
        }

    def allocate(self, total_budget: float, funds: list[dict], mode: str = "equal") -> list[dict]:
        """资金分配"""
        if not funds:
            return []

        results = []
        if mode == "equal":
            per_fund = total_budget / len(funds)
            for f in funds:
                buy = self.compute_buy(f["buy_price"], per_fund)
                results.append({
                    "code": f["code"],
                    "budget": round(per_fund, 2),
                    "shares": buy["shares"],
                    "total_cost": buy["total_cost"],
                    "commission": buy["commission"],
                })
        return results
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest src-python/tests/test_cost.py -v
```
Expected: 8 passed

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/scoring/cost.py src-python/tests/test_cost.py
git commit -m "feat: add cost calculator with budget allocation and fee warning"
```
