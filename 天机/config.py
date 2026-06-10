"""
天机 - 配置管理模块
支持 YAML 配置文件 + 环境变量覆盖
"""

import os
import yaml
from pathlib import Path
from typing import Optional


class Config:
    """全局配置管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config = {}
        self._load_defaults()
        self._load_from_file()
        self._load_from_env()

    def _load_defaults(self):
        """加载默认配置"""
        self._config = {
            "llm": {
                "backend": "deepseek",
                "base_url": "https://api.deepseek.com",
                "api_key": "",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.95,
            },
            "tools": {
                "allowed_commands": [],
                "command_timeout": 120,
                "web_search": {
                    "engine": "duckduckgo",
                    "max_results": 8,
                },
                "file": {
                    "max_file_size": 10 * 1024 * 1024,
                    "workspace_root": "",
                },
            },
            "memory": {
                "max_turns": 50,
                "persistent": True,
                "storage_path": "memory.json",
            },
            "log_level": "INFO",
        }

    def _load_from_file(self):
        """从 YAML 文件加载配置"""
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    self._deep_merge(self._config, file_config)

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 通用 API Key
        env_api_key = os.getenv("TIANJI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if env_api_key:
            self._config["llm"]["api_key"] = env_api_key

        # OpenAI Key
        env_openai_key = os.getenv("OPENAI_API_KEY")
        if env_openai_key and not self._config["llm"]["api_key"]:
            self._config["llm"]["api_key"] = env_openai_key

        # 日志级别
        env_log = os.getenv("TIANJI_LOG_LEVEL")
        if env_log:
            self._config["log_level"] = env_log.upper()

    def _deep_merge(self, base: dict, override: dict):
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    # ---- 便捷访问属性 ----

    @property
    def llm_backend(self) -> str:
        return self._config["llm"]["backend"]

    @property
    def llm_base_url(self) -> str:
        return self._config["llm"]["base_url"]

    @property
    def llm_api_key(self) -> Optional[str]:
        return self._config["llm"]["api_key"] or None

    @property
    def llm_model(self) -> str:
        return self._config["llm"]["model"]

    @property
    def llm_temperature(self) -> float:
        return float(self._config["llm"]["temperature"])

    @property
    def llm_max_tokens(self) -> int:
        return int(self._config["llm"]["max_tokens"])

    @property
    def llm_top_p(self) -> float:
        return float(self._config["llm"]["top_p"])

    @property
    def command_timeout(self) -> int:
        return int(self._config["tools"]["command_timeout"])

    @property
    def allowed_commands(self) -> list:
        return self._config["tools"]["allowed_commands"]

    @property
    def web_search_engine(self) -> str:
        return self._config["tools"]["web_search"]["engine"]

    @property
    def web_search_max_results(self) -> int:
        return int(self._config["tools"]["web_search"]["max_results"])

    @property
    def max_file_size(self) -> int:
        return int(self._config["tools"]["file"]["max_file_size"])

    @property
    def workspace_root(self) -> Optional[str]:
        root = self._config["tools"]["file"]["workspace_root"]
        return root if root else None

    @property
    def memory_max_turns(self) -> int:
        return int(self._config["memory"]["max_turns"])

    @property
    def memory_persistent(self) -> bool:
        return bool(self._config["memory"]["persistent"])

    @property
    def memory_storage_path(self) -> str:
        return self._config["memory"]["storage_path"]

    @property
    def log_level(self) -> str:
        return self._config["log_level"]

    def get(self, key: str, default=None):
        """通过点分隔的 key 获取配置，如 'llm.backend'"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def reload(self):
        """重新加载配置"""
        self._config = {}
        self._load_defaults()
        self._load_from_file()
        self._load_from_env()

    def to_dict(self) -> dict:
        """导出完整配置（屏蔽敏感信息）"""
        safe = __import__("copy").deepcopy(self._config)
        if safe.get("llm", {}).get("api_key"):
            key = safe["llm"]["api_key"]
            safe["llm"]["api_key"] = key[:8] + "..." if len(key) > 8 else "***"
        return safe


# 全局单例
config = Config()
