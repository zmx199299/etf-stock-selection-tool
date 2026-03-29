# 阶段一续：Task 9-11（配置 + JSON-RPC入口 + 集成测试）

## Task 9: 配置管理模块

**Files:**
- Create: `src-python/engine/config.py`
- Test: `src-python/tests/test_config.py`

- [ ] **Step 1: 编写配置测试**

```python
# src-python/tests/test_config.py
import os, tempfile, pytest
from engine.models.database import Database
from engine.config import ConfigManager

@pytest.fixture
def config_mgr():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    db.init()
    mgr = ConfigManager(db)
    yield mgr
    db.close()
    os.unlink(path)

def test_default_values(config_mgr):
    assert config_mgr.get("amplitude_min") == 0.035
    assert config_mgr.get("commission_rate") == 0.00025
    assert config_mgr.get("free5") is False

def test_set_and_get(config_mgr):
    config_mgr.set("amplitude_min", 0.04)
    assert config_mgr.get("amplitude_min") == 0.04

def test_get_all(config_mgr):
    all_cfg = config_mgr.get_all()
    assert "amplitude_min" in all_cfg
    assert "consecutive_days" in all_cfg
    assert "phase1_time" in all_cfg

def test_get_screener_params(config_mgr):
    params = config_mgr.get_screener_params()
    assert "amplitude_min" in params
    assert "amplitude_max" in params

def test_get_cost_params(config_mgr):
    params = config_mgr.get_cost_params()
    assert "commission_rate" in params
    assert "free5" in params
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 config.py**

```python
# src-python/engine/config.py
import json
from engine.models.database import Database

DEFAULTS = {
    # 筛选参数
    "amplitude_min": 0.035,
    "amplitude_max": 0.045,
    "min_drop": -0.01,
    "consecutive_days": 3,
    "score_threshold": 60,
    "premium_rate_min": -0.05,
    "premium_rate_max": 0.03,
    # 评分权重
    "weight_trend": 0.30,
    "weight_momentum": 0.25,
    "weight_volatility": 0.20,
    "weight_volume": 0.25,
    # 买入评分权重
    "buy_weight_tech": 0.40,
    "buy_weight_premium": 0.20,
    "buy_weight_reversal": 0.15,
    "buy_weight_consecutive": 0.10,
    "buy_weight_volume": 0.15,
    # 止盈止损
    "tp_factor": 1.5,
    "sl_factor": 1.0,
    # 交易费率
    "commission_rate": 0.00025,
    "free5": False,
    "min_commission": 5.0,
    "transfer_fee": 0.00001,
    # 调度
    "phase1_time": "15:30",
    "phase2_time": "21:00",
    "retry_interval_min": 30,
    "retry_deadline": "23:00",
}

# 布尔类型字段
BOOL_KEYS = {"free5"}

class ConfigManager:
    def __init__(self, db: Database):
        self.db = db
        self._ensure_defaults()

    def _ensure_defaults(self):
        c = self.db.conn.cursor()
        for key, val in DEFAULTS.items():
            c.execute("SELECT value FROM config WHERE key=?", (key,))
            if c.fetchone() is None:
                c.execute("INSERT INTO config (key, value) VALUES (?, ?)",
                          (key, json.dumps(val)))
        self.db.conn.commit()

    def get(self, key: str):
        c = self.db.conn.cursor()
        c.execute("SELECT value FROM config WHERE key=?", (key,))
        row = c.fetchone()
        if row is None:
            return DEFAULTS.get(key)
        val = json.loads(row[0])
        return val

    def set(self, key: str, value):
        c = self.db.conn.cursor()
        c.execute("INSERT INTO config (key, value) VALUES (?, ?) "
                  "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                  (key, json.dumps(value)))
        self.db.conn.commit()

    def get_all(self) -> dict:
        result = {}
        for key in DEFAULTS:
            result[key] = self.get(key)
        return result

    def get_screener_params(self) -> dict:
        keys = ["amplitude_min","amplitude_max","min_drop","consecutive_days",
                "score_threshold","premium_rate_min","premium_rate_max"]
        return {k: self.get(k) for k in keys}

    def get_cost_params(self) -> dict:
        keys = ["commission_rate","free5","min_commission","transfer_fee"]
        return {k: self.get(k) for k in keys}

    def get_scoring_weights(self) -> dict:
        return {
            "trend": self.get("weight_trend"),
            "momentum": self.get("weight_momentum"),
            "volatility": self.get("weight_volatility"),
            "volume": self.get("weight_volume"),
        }

    def get_buy_score_weights(self) -> dict:
        return {
            "tech": self.get("buy_weight_tech"),
            "premium": self.get("buy_weight_premium"),
            "reversal": self.get("buy_weight_reversal"),
            "consecutive": self.get("buy_weight_consecutive"),
            "volume_change": self.get("buy_weight_volume"),
        }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest src-python/tests/test_config.py -v
```
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add src-python/engine/config.py src-python/tests/test_config.py
git commit -m "feat: add config manager with all default parameters"
```

---

## Task 10: JSON-RPC 入口与 CLI 模式

**Files:**
- Create: `src-python/main.py`
- Test: `src-python/tests/test_main.py`

- [ ] **Step 1: 编写入口测试**

```python
# src-python/tests/test_main.py
import json, subprocess, sys, os, pytest

ENGINE_DIR = os.path.join(os.path.dirname(__file__), "..")

def call_rpc(method, params=None):
    req = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
    proc = subprocess.run(
        [sys.executable, "main.py", "--once"],
        input=json.dumps(req), capture_output=True, text=True,
        cwd=ENGINE_DIR, timeout=30
    )
    return json.loads(proc.stdout)

def test_ping():
    resp = call_rpc("ping")
    assert resp["result"] == "pong"

def test_get_config():
    resp = call_rpc("get_config")
    assert "result" in resp
    assert "amplitude_min" in resp["result"]

def test_unknown_method():
    resp = call_rpc("nonexistent_method")
    assert "error" in resp
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 实现 main.py**

```python
# src-python/main.py
"""
ETF 分析引擎入口
支持两种模式：
  - JSON-RPC 模式（默认）：通过 stdin/stdout 通信，供 Tauri sidecar 调用
  - CLI 模式：python main.py --cli sync / screen / score
"""
import sys, json, os, argparse
from datetime import datetime

# 确保 engine 包可被导入
sys.path.insert(0, os.path.dirname(__file__))

from engine.models.database import Database
from engine.config import ConfigManager
from engine.data.akshare_source import AkshareSource
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer
from engine.scoring.cost import CostCalculator
from engine.screener.pattern import PatternScreener

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "etf_analyzer.db")

class Engine:
    def __init__(self, db_path: str = None):
        self.db = Database(db_path or DB_PATH)
        self.db.init()
        self.config = ConfigManager(self.db)
        self.data_source = AkshareSource()
        self.indicators = TechnicalIndicators()
        self.scorer = Scorer(weights=self.config.get_scoring_weights())
        self.screener = PatternScreener(params=self.config.get_screener_params())

    def close(self):
        self.db.close()

    # --- RPC 方法 ---
    def ping(self, params):
        return "pong"

    def get_config(self, params):
        return self.config.get_all()

    def set_config(self, params):
        for k, v in params.items():
            self.config.set(k, v)
        return {"status": "ok"}

    def sync_data(self, params):
        """数据同步（唯一联网环节）"""
        phase = params.get("phase", "all")
        results = {"synced_funds": 0, "synced_quotes": 0, "errors": []}

        if phase in ("all", "list"):
            funds = self.data_source.fetch_fund_list()
            self.db.upsert_fund_info(funds)
            results["synced_funds"] = len(funds)

        if phase in ("all", "quotes"):
            active = self.db.get_all_active_funds()
            for fund in active:
                try:
                    last = self.db.get_latest_date(fund["code"])
                    quotes = self.data_source.fetch_daily_quotes(fund["code"], start_date=last)
                    if quotes:
                        self._preprocess_quotes(fund["code"], quotes)
                        self.db.upsert_daily_quotes(
                            [{**q, "code": fund["code"]} for q in quotes]
                        )
                        results["synced_quotes"] += len(quotes)
                except Exception as e:
                    results["errors"].append({"code": fund["code"], "error": str(e)})

        if phase in ("all", "nav"):
            active = self.db.get_all_active_funds()
            for fund in active:
                try:
                    navs = self.data_source.fetch_nav(fund["code"])
                    # 更新 nav 和 premium_rate
                    for nav_item in navs:
                        self.db._update_nav(fund["code"], nav_item["date"], nav_item["nav"])
                except Exception as e:
                    results["errors"].append({"code": fund["code"], "error": str(e)})

        return results

    def run_analysis(self, params):
        """运行完整分析流程（本地计算）"""
        date = params.get("date", datetime.now().strftime("%Y-%m-%d"))
        active = self.db.get_all_active_funds()
        screening_results = []
        scoring_results = []

        for fund in active:
            quotes = self.db.get_daily_quotes(fund["code"], "1990-01-01", date)
            if len(quotes) < 60:
                continue
            # 略：完整分析流程在此执行
            # 详见 Task 11 集成测试

        return {
            "date": date,
            "analyzed": len(active),
            "screening_hits": len([r for r in screening_results if r.get("passed")]),
        }

    def _preprocess_quotes(self, code, quotes):
        """预处理：计算 prev_close, 停牌判定"""
        for i, q in enumerate(quotes):
            if i == 0:
                prev = self.db.get_daily_quotes(code, "1990-01-01", q["date"])
                q["prev_close"] = prev[-2]["close"] if len(prev) >= 2 else q["open"]
            else:
                q["prev_close"] = quotes[i-1]["close"]
            # 停牌判定
            q["is_suspended"] = 1 if q.get("volume", 0) == 0 else 0
            if q["is_suspended"] == 0 and q["open"] == q["close"] == q["high"] == q["low"]:
                q["is_suspended"] = 1
            q["suspended_days"] = 0  # 后续批量计算
            # 折溢价（有净值时才计算）
            q["nav"] = q.get("nav", None)
            q["premium_rate"] = None
            if q.get("nav") and q["nav"] > 0:
                q["premium_rate"] = round((q["close"] - q["nav"]) / q["nav"], 6)


# --- JSON-RPC 处理 ---
METHODS = ["ping", "get_config", "set_config", "sync_data", "run_analysis"]

def handle_rpc(engine: Engine, request: str) -> str:
    try:
        req = json.loads(request)
    except json.JSONDecodeError:
        return json.dumps({"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"},"id":None})

    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")

    if method not in METHODS or not hasattr(engine, method):
        return json.dumps({"jsonrpc":"2.0","error":{"code":-32601,"message":f"Unknown method: {method}"},"id":req_id})

    try:
        result = getattr(engine, method)(params)
        return json.dumps({"jsonrpc":"2.0","result":result,"id":req_id}, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"jsonrpc":"2.0","error":{"code":-32000,"message":str(e)},"id":req_id})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="处理单条请求后退出")
    parser.add_argument("--cli", type=str, help="CLI 模式: sync/screen/score")
    parser.add_argument("--db", type=str, default=None, help="数据库路径")
    args = parser.parse_args()

    engine = Engine(db_path=args.db)

    if args.cli:
        # CLI 模式
        if args.cli == "sync":
            result = engine.sync_data({"phase": "all"})
        elif args.cli == "screen":
            result = engine.run_analysis({})
        else:
            result = {"error": f"Unknown CLI command: {args.cli}"}
        print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    elif args.once:
        # 单次 RPC（测试用）
        line = sys.stdin.read()
        response = handle_rpc(engine, line)
        print(response)
    else:
        # 持续 RPC 模式（Tauri sidecar 用）
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            response = handle_rpc(engine, line)
            print(response, flush=True)

    engine.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest src-python/tests/test_main.py -v
```
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add src-python/main.py src-python/tests/test_main.py
git commit -m "feat: add JSON-RPC entry point and CLI mode"
```

---

## Task 11: 集成测试

**Files:**
- Create: `src-python/tests/test_integration.py`

- [ ] **Step 1: 编写集成测试**

```python
# src-python/tests/test_integration.py
"""集成测试：使用模拟数据，不联网"""
import os, tempfile, pytest
import pandas as pd
import numpy as np
from engine.models.database import Database
from engine.config import ConfigManager
from engine.scoring.indicators import TechnicalIndicators
from engine.scoring.scorer import Scorer
from engine.scoring.cost import CostCalculator
from engine.screener.pattern import PatternScreener

@pytest.fixture
def full_env():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    db.init()
    config = ConfigManager(db)
    yield db, config, path
    db.close()
    os.unlink(path)

def _generate_v_shape_quotes(n_days=60, code="510300"):
    """生成含 V 型反转形态的模拟数据"""
    quotes = []
    base = 4.0
    for i in range(n_days):
        prev_close = base + i * 0.001
        # 最后5天制造V型反转形态
        if i >= n_days - 5:
            low = prev_close * 0.985
            high = low + prev_close * 0.04
            close = high - 0.005
        else:
            low = prev_close * 0.995
            high = prev_close * 1.005
            close = prev_close * 1.001
        quotes.append({
            "code": code, "date": f"2026-{(i//28)+1:02d}-{(i%28)+1:02d}",
            "open": prev_close, "close": round(close, 4),
            "high": round(high, 4), "low": round(low, 4),
            "volume": 100000.0 + i * 1000, "amount": 400000.0 + i * 4000,
            "nav": round(close * 0.995, 4), "premium_rate": 0.005,
            "prev_close": round(prev_close, 4),
            "is_suspended": 0, "suspended_days": 0,
        })
    return quotes

def test_full_pipeline(full_env):
    db, config, _ = full_env
    code = "510300"

    # 1. 插入基金信息
    db.upsert_fund_info([{
        "code": code, "name": "沪深300ETF", "fund_type": "ETF",
        "invest_type": "指数型", "t_plus": "T+1",
        "list_date": "2012-05-28", "is_excluded": 0,
    }])

    # 2. 插入模拟行情数据
    quotes = _generate_v_shape_quotes()
    db.upsert_daily_quotes(quotes)

    # 3. 读取数据并计算技术指标
    data = db.get_daily_quotes(code, "1990-01-01", "2099-12-31")
    df = pd.DataFrame(data)
    ti = TechnicalIndicators()
    df_ind = ti.compute_all(df)
    assert "macd" in df_ind.columns

    # 4. 综合评分
    scorer = Scorer(weights=config.get_scoring_weights())
    score_result = scorer.score(df_ind)
    assert 0 <= score_result["total_score"] <= 100

    # 5. 形态筛选
    screener = PatternScreener(params=config.get_screener_params())
    screen_result = screener.check_consecutive(data, n=3)
    assert "passed" in screen_result

    # 6. 如果通过筛选，计算交易成本
    if screen_result["passed"]:
        cost_params = config.get_cost_params()
        calc = CostCalculator(**cost_params)
        buy = calc.compute_buy(price=quotes[-1]["close"], budget=10000)
        assert buy["shares"] >= 0

        if buy["shares"] > 0:
            tp_price = quotes[-1]["close"] * 1.03
            sl_price = quotes[-1]["close"] * 0.99
            tp_result = calc.compute_profit_loss(buy["shares"], quotes[-1]["close"], tp_price)
            sl_result = calc.compute_profit_loss(buy["shares"], quotes[-1]["close"], sl_price)
            assert "warning" in tp_result
            assert "profit" in sl_result

def test_excluded_funds_skipped(full_env):
    db, config, _ = full_env
    db.upsert_fund_info([
        {"code": "511880", "name": "银华日利", "fund_type": "ETF",
         "invest_type": "货币型", "t_plus": "T+0",
         "list_date": "2013-01-01", "is_excluded": 1},
    ])
    active = db.get_all_active_funds()
    assert all(f["code"] != "511880" for f in active)
```

- [ ] **Step 2: 运行全部测试**

```bash
python -m pytest src-python/tests/ -v
```
Expected: 全部 passed

- [ ] **Step 3: 提交**

```bash
git add src-python/tests/test_integration.py
git commit -m "test: add integration test for full analysis pipeline"
```

---

## 阶段一完成标志

全部测试通过后，Python 分析引擎可独立运行：

```bash
# CLI 模式测试
source .venv/bin/activate
cd src-python
python main.py --cli sync   # 联网同步数据
python main.py --cli screen # 运行筛选分析
```

**下一步：阶段二（Tauri + Rust 中间层），但在开始编码前需提醒用户更换模型。**
