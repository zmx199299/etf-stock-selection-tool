import json
import pytest
from engine.server import JSONRPCServer

def test_handle_valid_request():
    server = JSONRPCServer()
    # Mock a simple ping method
    server.register_method("ping", lambda: "pong")
    
    req_str = json.dumps({"jsonrpc": "2.0", "method": "ping", "id": 1})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert res["jsonrpc"] == "2.0"
    assert res["id"] == 1
    assert res["result"] == "pong"
    assert "error" not in res

def test_handle_invalid_json():
    server = JSONRPCServer()
    req_str = "{invalid_json: true"
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert res["jsonrpc"] == "2.0"
    assert res["error"]["code"] == -32700
    assert "Parse error" in res["error"]["message"]

def test_handle_method_not_found():
    server = JSONRPCServer()
    req_str = json.dumps({"jsonrpc": "2.0", "method": "unknown_method", "id": 2})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert res["jsonrpc"] == "2.0"
    assert res["id"] == 2
    assert res["error"]["code"] == -32601
    assert "Method not found" in res["error"]["message"]

def test_handle_method_with_params():
    server = JSONRPCServer()
    server.register_method("add", lambda a, b: a + b)
    
    req_str = json.dumps({"jsonrpc": "2.0", "method": "add", "params": {"a": 2, "b": 3}, "id": 3})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert res["result"] == 5

def test_handle_method_exception():
    server = JSONRPCServer()
    def raise_err():
        raise ValueError("test error")
    server.register_method("fail", raise_err)
    
    req_str = json.dumps({"jsonrpc": "2.0", "method": "fail", "id": 4})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert res["error"]["code"] == -32000 # generic server error
    assert "test error" in res["error"]["message"]

def test_fetch_legal_tax_rates():
    # 测试获取法定税率的内置方法
    server = JSONRPCServer()
    # 模拟在 main.py 中的注册过程
    from engine.server import fetch_legal_tax_rates
    server.register_method("fetch_legal_tax_rates", fetch_legal_tax_rates)
    
    req_str = json.dumps({"jsonrpc": "2.0", "method": "fetch_legal_tax_rates", "id": 5})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert "error" not in res
    assert res["result"]["etf"]["stamp_duty"] == 0.0
    assert res["result"]["lof"]["stamp_duty"] == 0.0
    assert res["result"]["stock"]["stamp_duty"] == 0.5

def test_get_fund_list():
    server = JSONRPCServer()
    from engine.server import get_fund_list
    server.register_method("get_fund_list", get_fund_list)
    
    req_str = json.dumps({"jsonrpc": "2.0", "method": "get_fund_list", "id": 6})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert "error" not in res
    assert isinstance(res["result"], list)
    assert len(res["result"]) > 0
    assert "code" in res["result"][0]
    assert "macd" in res["result"][0]

def test_get_dashboard_signals():
    server = JSONRPCServer()
    from engine.server import get_dashboard_signals
    server.register_method("get_dashboard_signals", get_dashboard_signals)
    
    req_str = json.dumps({"jsonrpc": "2.0", "method": "get_dashboard_signals", "id": 7})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert "error" not in res
    assert isinstance(res["result"], list)
    assert len(res["result"]) > 0
    item = res["result"][0]
    required_fields = ["code", "name", "t_plus", "current_price", "buy_price",
                      "sell_price", "stop_loss", "latest_nav", "nav_date",
                      "premium_rate", "buyable_shares", "expected_profit",
                      "expected_profit_pct", "max_loss", "max_loss_pct"]
    for field in required_fields:
        assert field in item, f"Missing field: {field}"

def test_get_screening_results():
    server = JSONRPCServer()
    from engine.server import get_screening_results
    server.register_method("get_screening_results", get_screening_results)
    
    req_str = json.dumps({"jsonrpc": "2.0", "method": "get_screening_results", "id": 8})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert "error" not in res
    assert isinstance(res["result"], list)
    assert len(res["result"]) > 0
    assert "code" in res["result"][0]
    assert "strength" in res["result"][0]

def test_create_real_server():
    from engine.server import create_real_server
    from unittest.mock import Mock
    
    db_mock = Mock()
    source_mock = Mock()
    server = create_real_server(db_mock, source_mock)
    
    # Check if get_scoring_data is registered
    assert "get_scoring_data" in server.methods

def test_get_scheduler_data():
    server = JSONRPCServer()
    from engine.server import get_scheduler_data
    server.register_method("get_scheduler_data", get_scheduler_data)
    
    req_str = json.dumps({"jsonrpc": "2.0", "method": "get_scheduler_data", "id": 10})
    res_str = server.handle_request(req_str)
    res = json.loads(res_str)
    
    assert "error" not in res
    assert "tasks" in res["result"]
    assert "logs" in res["result"]
    assert len(res["result"]["tasks"]) > 0

