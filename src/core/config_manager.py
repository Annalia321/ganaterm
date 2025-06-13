#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器 - 处理配置相关的功能
"""

import os
import json
from typing import Dict, Any, Optional, Union, List
from dotenv import load_dotenv

class ConfigManager:
    """配置管理器，处理配置相关的功能"""
    
    def __init__(self, config_dir: str):
        """初始化配置管理器
        
        Args:
            config_dir: 配置目录路径
        """
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        self.env_file = os.path.join(config_dir, ".env")
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 加载环境变量
        self._load_env()
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化默认配置
        self._init_default_config()
    
    def _load_env(self) -> None:
        """加载环境变量"""
        # 首先尝试加载.env文件
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
        
        # 然后加载系统环境变量
        load_dotenv(override=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            配置字典
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件出错: {e}")
        return {}
    
    def _init_default_config(self) -> None:
        """初始化默认配置"""
        default_config = {
            "api": {
                "openai": {
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                    "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                    "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
                },
                "deepseek": {
                    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                    "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                    "temperature": float(os.getenv("DEEPSEEK_TEMPERATURE", "0.7")),
                    "max_tokens": int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000"))
                }
            },
            "memory": {
                "max_short_term": int(os.getenv("MAX_SHORT_TERM_MEMORY", "20")),
                "max_mid_term": int(os.getenv("MAX_MID_TERM_MEMORY", "50")),
                "max_long_term": int(os.getenv("MAX_LONG_TERM_MEMORY", "100")),
                "importance_threshold": float(os.getenv("MEMORY_IMPORTANCE_THRESHOLD", "0.3"))
            },
            "ui": {
                "theme": os.getenv("UI_THEME", "light"),
                "language": os.getenv("UI_LANGUAGE", "zh-CN"),
                "show_timestamps": os.getenv("SHOW_TIMESTAMPS", "true").lower() == "true",
                "enable_rich_text": os.getenv("ENABLE_RICH_TEXT", "true").lower() == "true"
            },
            "network": {
                "proxy": {
                    "http": os.getenv("HTTP_PROXY", ""),
                    "https": os.getenv("HTTPS_PROXY", "")
                },
                "timeout": int(os.getenv("REQUEST_TIMEOUT", "30")),
                "retry_count": int(os.getenv("REQUEST_RETRY_COUNT", "3"))
            },
            "system": {
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "data_dir": os.getenv("DATA_DIR", os.path.join(self.config_dir, "data")),
                "cache_dir": os.getenv("CACHE_DIR", os.path.join(self.config_dir, "cache"))
            }
        }
        
        # 更新配置
        self._update_config(default_config)
    
    def _update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            new_config: 新的配置字典
        """
        def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    d[k] = deep_update(d[k], v)
                else:
                    d[k] = v
            return d
        
        self.config = deep_update(self.config, new_config)
        self._save_config()
    
    def _save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件出错: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 遍历到倒数第二层
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置最后一层的值
        config[keys[-1]] = value
        
        # 保存配置
        self._save_config()
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """批量更新配置
        
        Args:
            config_dict: 配置字典
        """
        self._update_config(config_dict)
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """获取API配置
        
        Args:
            api_name: API名称
            
        Returns:
            API配置字典
        """
        return self.get(f"api.{api_name}", {})
    
    def get_memory_config(self) -> Dict[str, Any]:
        """获取记忆配置
        
        Returns:
            记忆配置字典
        """
        return self.get("memory", {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置
        
        Returns:
            UI配置字典
        """
        return self.get("ui", {})
    
    def get_network_config(self) -> Dict[str, Any]:
        """获取网络配置
        
        Returns:
            网络配置字典
        """
        return self.get("network", {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置
        
        Returns:
            系统配置字典
        """
        return self.get("system", {})
    
    def get_proxy_config(self) -> Dict[str, str]:
        """获取代理配置
        
        Returns:
            代理配置字典
        """
        proxy_config = self.get("network.proxy", {})
        return {
            "http": proxy_config.get("http", ""),
            "https": proxy_config.get("https", "")
        }
    
    def is_debug_mode(self) -> bool:
        """检查是否处于调试模式
        
        Returns:
            是否为调试模式
        """
        return self.get("system.debug", False)
    
    def get_log_level(self) -> str:
        """获取日志级别
        
        Returns:
            日志级别
        """
        return self.get("system.log_level", "INFO")
    
    def get_data_dir(self) -> str:
        """获取数据目录
        
        Returns:
            数据目录路径
        """
        data_dir = self.get("system.data_dir", os.path.join(self.config_dir, "data"))
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    
    def get_cache_dir(self) -> str:
        """获取缓存目录
        
        Returns:
            缓存目录路径
        """
        cache_dir = self.get("system.cache_dir", os.path.join(self.config_dir, "cache"))
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    
    def get_theme(self) -> str:
        """获取主题
        
        Returns:
            主题名称
        """
        return self.get("ui.theme", "light")
    
    def get_language(self) -> str:
        """获取语言
        
        Returns:
            语言代码
        """
        return self.get("ui.language", "zh-CN")
    
    def show_timestamps(self) -> bool:
        """检查是否显示时间戳
        
        Returns:
            是否显示时间戳
        """
        return self.get("ui.show_timestamps", True)
    
    def enable_rich_text(self) -> bool:
        """检查是否启用富文本
        
        Returns:
            是否启用富文本
        """
        return self.get("ui.enable_rich_text", True)
    
    def get_request_timeout(self) -> int:
        """获取请求超时时间
        
        Returns:
            超时时间（秒）
        """
        return self.get("network.timeout", 30)
    
    def get_retry_count(self) -> int:
        """获取重试次数
        
        Returns:
            重试次数
        """
        return self.get("network.retry_count", 3)
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """获取模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置字典
        """
        return self.get(f"api.{model_name}", {})
    
    def get_model_priority(self) -> List[str]:
        """获取模型优先级列表
        
        Returns:
            模型优先级列表
        """
        return self.get("api.model_priority", ["openai", "deepseek"])
    
    def set_model_priority(self, priority: List[str]) -> None:
        """设置模型优先级列表
        
        Args:
            priority: 模型优先级列表
        """
        self.set("api.model_priority", priority)
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表
        
        Returns:
            可用模型列表
        """
        return list(self.get("api", {}).keys())
    
    def is_model_available(self, model_name: str) -> bool:
        """检查模型是否可用
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型是否可用
        """
        model_config = self.get_model_config(model_name)
        return bool(model_config.get("api_key"))
    
    def get_next_available_model(self) -> Optional[str]:
        """获取下一个可用的模型
        
        Returns:
            可用模型名称，如果没有则返回None
        """
        for model in self.get_model_priority():
            if self.is_model_available(model):
                return model
        return None 