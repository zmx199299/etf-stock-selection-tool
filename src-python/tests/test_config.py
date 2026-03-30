import os
import json
import pytest
from pathlib import Path
from engine.utils.config import ConfigManager

@pytest.fixture
def temp_config_file(tmp_path):
    config_data = {
        "trading": {
            "budget": 100000.0,
            "commission_rate": 0.0001,
            "min_commission": 0.0, # 免5
            "stamp_duty": 0.001
        },
        "analysis": {
            "score_threshold": 60,
            "target_profit_rate": 0.05,
            "stop_loss_rate": 0.03
        }
    }
    file_path = tmp_path / "config.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f)
    return file_path

def test_load_config(temp_config_file):
    # 测试加载配置
    manager = ConfigManager(str(temp_config_file))
    config = manager.load()
    
    assert config["trading"]["budget"] == 100000.0
    assert config["trading"]["min_commission"] == 0.0
    assert config["analysis"]["score_threshold"] == 60

def test_get_value(temp_config_file):
    # 测试获取特定配置值
    manager = ConfigManager(str(temp_config_file))
    
    budget = manager.get("trading.budget")
    assert budget == 100000.0
    
    # 获取不存在的值应返回默认值
    default_val = manager.get("trading.not_exist", 5.0)
    assert default_val == 5.0

def test_save_config(tmp_path):
    # 测试保存配置
    file_path = tmp_path / "new_config.json"
    manager = ConfigManager(str(file_path))
    
    new_data = {"test": {"key": "value"}}
    manager.update(new_data)
    manager.save()
    
    assert os.path.exists(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["test"]["key"] == "value"
