import json
import os

class ConfigManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.config = {}

    def load(self):
        """加载 JSON 配置文件并返回配置字典"""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        return self.config

    def get(self, key, default=None):
        """使用点分割的键名获取嵌套的配置值 (例如 'trading.budget')"""
        if not self.config:
            self.load()
            
        keys = key.split('.')
        val = self.config
        
        try:
            for k in keys:
                val = val[k]
            return val
        except (KeyError, TypeError):
            return default

    def update(self, new_data):
        """更新内存中的配置字典"""
        self.config.update(new_data)

    def save(self):
        """将内存中的配置写入 JSON 文件"""
        directory = os.path.dirname(os.path.abspath(self.filepath))
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)
