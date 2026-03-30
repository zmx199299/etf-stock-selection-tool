import json
import traceback

def fetch_legal_tax_rates():
    """
    模拟联网查询最新的法定印花税率。
    - 自2023年8月28日起，A股交易印花税减半征收，单边收取，税率为 0.5‰
    - 场内基金（ETF/LOF）依法免征印花税
    """
    return {
        "etf": {"stamp_duty": 0.0},
        "lof": {"stamp_duty": 0.0},
        "stock": {"stamp_duty": 0.5}
    }

def get_fund_list():
    # TODO: Replace with real DB query when sync engine is built
    return [
        {
            "code": "510300",
            "name": "沪深300ETF",
            "prevClose": 4.100,
            "open": 4.105,
            "close": 4.123,
            "high": 4.150,
            "low": 4.080,
            "volatility": (4.150 - 4.080) / 4.080,
            "macd": { "signal": "bullish", "value": "金叉" },
            "rsi": { "signal": "neutral", "value": "52" },
            "boll": { "signal": "bullish", "value": "中轨" },
            "ma5": { "signal": "bullish", "value": "上穿" },
            "ma20": { "signal": "neutral", "value": "粘合" },
            "score": 9,
        },
        {
            "code": "159915",
            "name": "创业板ETF",
            "prevClose": 2.240,
            "open": 2.245,
            "close": 2.256,
            "high": 2.280,
            "low": 2.230,
            "volatility": (2.280 - 2.230) / 2.230,
            "macd": { "signal": "bullish", "value": "红柱" },
            "rsi": { "signal": "bullish", "value": "68" },
            "boll": { "signal": "bullish", "value": "下轨" },
            "ma5": { "signal": "bullish", "value": "多头" },
            "ma20": { "signal": "bullish", "value": "向上" },
            "score": 10,
        },
        {
            "code": "510500",
            "name": "中证500ETF",
            "prevClose": 6.800,
            "open": 6.790,
            "close": 6.789,
            "high": 6.820,
            "low": 6.750,
            "volatility": (6.820 - 6.750) / 6.750,
            "macd": { "signal": "bearish", "value": "死叉" },
            "rsi": { "signal": "neutral", "value": "48" },
            "boll": { "signal": "neutral", "value": "中轨" },
            "ma5": { "signal": "bearish", "value": "下穿" },
            "ma20": { "signal": "neutral", "value": "粘合" },
            "score": 3,
        },
        {
            "code": "588000",
            "name": "科创50ETF",
            "prevClose": 1.050,
            "open": 1.045,
            "close": 1.030,
            "high": 1.060,
            "low": 1.020,
            "volatility": (1.060 - 1.020) / 1.020,
            "macd": { "signal": "bearish", "value": "绿柱" },
            "rsi": { "signal": "bearish", "value": "25" },
            "boll": { "signal": "bearish", "value": "上轨" },
            "ma5": { "signal": "bearish", "value": "空头" },
            "ma20": { "signal": "bearish", "value": "向下" },
            "score": 1,
        }
    ]

def get_dashboard_signals():
    return [
        {
            "code": "512980",
            "name": "传媒ETF广发",
            "t_plus": "T+1",
            "current_price": 0.985,
            "buy_price": 0.980,
            "sell_price": 0.987,
            "stop_loss": 0.955,
            "latest_nav": 0.986,
            "nav_date": "2026-03-27",
            "premium_rate": -0.07,
            "buyable_shares": 10200,
            "expected_profit": 61.40,
            "expected_profit_pct": 0.61,
            "max_loss": 265.00,
            "max_loss_pct": 2.65
        },
        {
            "code": "512480",
            "name": "半导体ETF国联安",
            "t_plus": "T+1",
            "current_price": 1.468,
            "buy_price": 1.458,
            "sell_price": 1.470,
            "stop_loss": 1.424,
            "latest_nav": 1.468,
            "nav_date": "2026-03-27",
            "premium_rate": 0.00,
            "buyable_shares": 6800,
            "expected_profit": 71.60,
            "expected_profit_pct": 0.72,
            "max_loss": 241.20,
            "max_loss_pct": 2.43
        },
        {
            "code": "159928",
            "name": "消费ETF汇添富",
            "t_plus": "T+1",
            "current_price": 0.752,
            "buy_price": 0.745,
            "sell_price": 0.754,
            "stop_loss": 0.723,
            "latest_nav": 0.752,
            "nav_date": "2026-03-27",
            "premium_rate": -0.03,
            "buyable_shares": 13400,
            "expected_profit": 110.60,
            "expected_profit_pct": 1.11,
            "max_loss": 304.80,
            "max_loss_pct": 3.05
        },
        {
            "code": "513050",
            "name": "中概互联网ETF易方达",
            "t_plus": "T+0",
            "current_price": 1.211,
            "buy_price": 1.201,
            "sell_price": 1.213,
            "stop_loss": 1.175,
            "latest_nav": 1.208,
            "nav_date": "2026-03-26",
            "premium_rate": 0.26,
            "buyable_shares": 8300,
            "expected_profit": 89.60,
            "expected_profit_pct": 0.90,
            "max_loss": 225.80,
            "max_loss_pct": 2.26
        },
        {
            "code": "518880",
            "name": "黄金ETF华安",
            "t_plus": "T+0",
            "current_price": 9.494,
            "buy_price": 9.419,
            "sell_price": 9.504,
            "stop_loss": 9.209,
            "latest_nav": 9.482,
            "nav_date": "2026-03-27",
            "premium_rate": 0.13,
            "buyable_shares": 1000,
            "expected_profit": 75.00,
            "expected_profit_pct": 0.80,
            "max_loss": 220.00,
            "max_loss_pct": 2.33
        }
    ]

def get_screening_results():
    return [
        { "code": "510300", "name": "沪深300ETF", "pattern": "V型反转", "strength": 85, "price": 4.123 },
        { "code": "159915", "name": "创业板ETF", "pattern": "V型反转", "strength": 92, "price": 2.256 },
        { "code": "510500", "name": "中证500ETF", "pattern": "V型反转", "strength": 70, "price": 6.789 },
        { "code": "588000", "name": "科创50ETF", "pattern": "V型反转", "strength": 78, "price": 1.023 },
    ]

def get_scoring_data(code: str = "510300"):
    # Mock data based on requested code or default
    return {
        "code": code,
        "name": "沪深300ETF" if code == "510300" else f"基金{code}",
        "price": 4.123,
        "change": 1.25,
        "signal": "强烈看多",
        "trendScore": 80,
        "momentumScore": 75,
        "volatilityScore": 70,
        "volumeScore": 65,
        "adviceAmount": 24000,
        "estimateFee": 10.50,
        "stopLoss": 3.98,
        "takeProfit": 4.35,
    }

def get_scheduler_data():
    return {
        "tasks": [
            { "id": 1, "name": "同步基金列表", "cron": "每日 00:00", "enabled": True },
            { "id": 2, "name": "初步行情筛选", "cron": "每日 15:30", "enabled": True },
            { "id": 3, "name": "净值更新与折溢价计算", "cron": "每日 21:00", "enabled": True },
        ],
        "logs": [
            { "id": 1, "time": "2026-03-29 21:05:12", "taskName": "净值更新与折溢价计算", "status": "成功", "message": "共更新 512 只基金净值" },
            { "id": 2, "time": "2026-03-29 15:32:45", "taskName": "初步行情筛选", "status": "成功", "message": "筛选出 34 只形态匹配基金" },
            { "id": 3, "time": "2026-03-29 00:01:23", "taskName": "同步基金列表", "status": "成功", "message": "列表无变化" },
        ]
    }

class JSONRPCServer:
    def __init__(self):
        self.methods = {}

    def register_method(self, name: str, func: callable):
        self.methods[name] = func

    def _make_error(self, code: int, message: str, req_id=None):
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": req_id
        }

    def _make_success(self, result, req_id):
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": req_id
        }

    def handle_request(self, req_str: str) -> str:
        try:
            req = json.loads(req_str)
        except json.JSONDecodeError:
            return json.dumps(self._make_error(-32700, "Parse error"))
            
        req_id = req.get("id")

        if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or "method" not in req:
            return json.dumps(self._make_error(-32600, "Invalid Request", req_id))

        method_name = req["method"]
        if method_name not in self.methods:
            return json.dumps(self._make_error(-32601, f"Method not found: {method_name}", req_id))

        params = req.get("params", {})
        func = self.methods[method_name]

        try:
            if isinstance(params, dict):
                result = func(**params)
            elif isinstance(params, list):
                result = func(*params)
            else:
                result = func()
            return json.dumps(self._make_success(result, req_id))
        except Exception as e:
            # -32000 to -32099 are reserved for implementation-defined server-errors
            # tb = traceback.format_exc() # Useful for debugging but maybe not expose everything to client
            return json.dumps(self._make_error(-32000, str(e), req_id))

    def run_stdio(self): # pragma: no cover
        """
        Main loop for standard I/O communication (used by Tauri sidecar).
        """
        import sys
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            response = self.handle_request(line)
            sys.stdout.write(response + "\n")
            sys.stdout.flush()
