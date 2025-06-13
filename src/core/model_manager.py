#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型管理器 - 处理AI模型调用相关的功能
"""

import os
import json
import time
import requests
from typing import Optional, Dict, List, Any, Union
from datetime import datetime

class ModelManager:
    """模型管理器，处理AI模型调用相关的功能"""
    
    def __init__(self, config_manager: Any, logger: Any):
        """初始化模型管理器
        
        Args:
            config_manager: 配置管理器实例
            logger: 日志管理器实例
        """
        self.config_manager = config_manager
        self.logger = logger
        
        # 初始化模型配置
        self.models = self._init_models()
        self.current_model = self._get_default_model()
        
        # 初始化请求会话
        self.session = requests.Session()
        self._setup_session()
    
    def _init_models(self) -> Dict[str, Dict[str, Any]]:
        """初始化模型配置
        
        Returns:
            模型配置字典
        """
        return {
            "openai": {
                "name": "OpenAI",
                "api_key": self.config_manager.get_api_key("openai"),
                "api_base": self.config_manager.get_api_endpoint("openai"),
                "models": ["gpt-3.5-turbo", "gpt-4"],
                "default_model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 30
            },
            "deepseek": {
                "name": "DeepSeek",
                "api_key": self.config_manager.get_api_key("deepseek"),
                "api_base": self.config_manager.get_api_endpoint("deepseek"),
                "models": ["deepseek-chat"],
                "default_model": "deepseek-chat",
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 30
            }
        }
    
    def _get_default_model(self) -> str:
        """获取默认模型
        
        Returns:
            默认模型名称
        """
        return self.config_manager.get_model_priority()[0]
    
    def _setup_session(self) -> None:
        """设置请求会话"""
        # 设置代理
        proxies = self.config_manager.get_proxy_settings()
        if proxies:
            self.session.proxies.update(proxies)
        
        # 设置超时
        self.session.timeout = 30
        
        # 设置重试
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表
        
        Returns:
            可用模型列表
        """
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型信息字典
        """
        return self.models.get(model_name)
    
    def set_current_model(self, model_name: str) -> bool:
        """设置当前模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否设置成功
        """
        if model_name in self.models:
            self.current_model = model_name
            self.logger.info(f"已切换到模型: {model_name}")
            return True
        return False
    
    def get_current_model(self) -> str:
        """获取当前模型
        
        Returns:
            当前模型名称
        """
        return self.current_model
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """发送聊天请求
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Returns:
            响应结果
        """
        model_info = self.get_model_info(self.current_model)
        if not model_info:
            raise ValueError(f"模型不存在: {self.current_model}")
        
        # 准备请求参数
        params = {
            "model": model_info["default_model"],
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", model_info["max_tokens"]),
            "temperature": kwargs.get("temperature", model_info["temperature"])
        }
        
        # 记录API调用
        self.logger.log_api_call(
            self.current_model,
            "POST",
            f"{model_info['api_base']}/v1/chat/completions",
            params=params
        )
        
        try:
            # 发送请求
            start_time = time.time()
            response = self.session.post(
                f"{model_info['api_base']}/v1/chat/completions",
                headers={"Authorization": f"Bearer {model_info['api_key']}"},
                json=params,
                timeout=model_info["timeout"]
            )
            end_time = time.time()
            
            # 记录API响应
            self.logger.log_api_response(
                self.current_model,
                response.status_code,
                duration=end_time - start_time
            )
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "content": result["choices"][0]["message"]["content"],
                    "model": result["model"],
                    "usage": result["usage"]
                }
            else:
                error_msg = f"API请求失败: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('error', {}).get('message', '')}"
                except:
                    pass
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"模型调用失败: {self.current_model}", exc_info=True)
            raise
    
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """流式聊天请求
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Returns:
            响应生成器
        """
        model_info = self.get_model_info(self.current_model)
        if not model_info:
            raise ValueError(f"模型不存在: {self.current_model}")
        
        # 准备请求参数
        params = {
            "model": model_info["default_model"],
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", model_info["max_tokens"]),
            "temperature": kwargs.get("temperature", model_info["temperature"]),
            "stream": True
        }
        
        # 记录API调用
        self.logger.log_api_call(
            self.current_model,
            "POST",
            f"{model_info['api_base']}/v1/chat/completions",
            params=params
        )
        
        try:
            # 发送请求
            response = self.session.post(
                f"{model_info['api_base']}/v1/chat/completions",
                headers={"Authorization": f"Bearer {model_info['api_key']}"},
                json=params,
                timeout=model_info["timeout"],
                stream=True
            )
            
            # 记录API响应
            self.logger.log_api_response(
                self.current_model,
                response.status_code
            )
            
            # 处理响应
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8").replace("data: ", ""))
                            if data.get("choices"):
                                yield data["choices"][0]["delta"].get("content", "")
                        except:
                            continue
            else:
                error_msg = f"API请求失败: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('error', {}).get('message', '')}"
                except:
                    pass
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"模型调用失败: {self.current_model}", exc_info=True)
            raise
    
    def get_model_usage(self) -> Dict[str, Any]:
        """获取模型使用情况
        
        Returns:
            使用情况统计
        """
        usage = {}
        for model_name in self.get_available_models():
            model_info = self.get_model_info(model_name)
            if not model_info:
                continue
            
            try:
                response = self.session.get(
                    f"{model_info['api_base']}/v1/usage",
                    headers={"Authorization": f"Bearer {model_info['api_key']}"},
                    timeout=model_info["timeout"]
                )
                
                if response.status_code == 200:
                    usage[model_name] = response.json()
                else:
                    self.logger.warning(
                        f"获取使用情况失败: {model_name}",
                        status_code=response.status_code
                    )
                    
            except Exception as e:
                self.logger.error(
                    f"获取使用情况异常: {model_name}",
                    exc_info=True
                )
        
        return usage
    
    def check_model_availability(self) -> Dict[str, bool]:
        """检查模型可用性
        
        Returns:
            模型可用性字典
        """
        availability = {}
        for model_name in self.get_available_models():
            model_info = self.get_model_info(model_name)
            if not model_info:
                availability[model_name] = False
                continue
            
            try:
                response = self.session.get(
                    f"{model_info['api_base']}/v1/models",
                    headers={"Authorization": f"Bearer {model_info['api_key']}"},
                    timeout=5
                )
                availability[model_name] = response.status_code == 200
            except:
                availability[model_name] = False
        
        return availability
    
    def get_model_capabilities(self) -> Dict[str, List[str]]:
        """获取模型能力
        
        Returns:
            模型能力字典
        """
        capabilities = {}
        for model_name in self.get_available_models():
            model_info = self.get_model_info(model_name)
            if not model_info:
                continue
            
            try:
                response = self.session.get(
                    f"{model_info['api_base']}/v1/models/{model_info['default_model']}",
                    headers={"Authorization": f"Bearer {model_info['api_key']}"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    model_data = response.json()
                    capabilities[model_name] = model_data.get("capabilities", [])
                else:
                    capabilities[model_name] = []
                    
            except:
                capabilities[model_name] = []
        
        return capabilities 