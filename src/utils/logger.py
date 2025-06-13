#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志管理器 - 处理日志相关的功能
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Optional, Union, Dict, Any
from logging.handlers import RotatingFileHandler

class Logger:
    """日志管理器，处理日志相关的功能"""
    
    def __init__(self, config_manager: Any):
        """初始化日志管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger("ganaterm")
        self.logger.setLevel(logging.DEBUG)
        
        # 获取日志配置
        self.log_level = self._get_log_level()
        self.log_dir = self._get_log_dir()
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        
        # 设置日志格式
        self.formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 初始化日志处理器
        self._init_handlers()
    
    def _get_log_level(self) -> int:
        """获取日志级别
        
        Returns:
            日志级别
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(self.config_manager.get_log_level(), logging.INFO)
    
    def _get_log_dir(self) -> str:
        """获取日志目录
        
        Returns:
            日志目录路径
        """
        log_dir = os.path.join(self.config_manager.get_data_dir(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    
    def _init_handlers(self) -> None:
        """初始化日志处理器"""
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        log_file = os.path.join(self.log_dir, "ganaterm.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
        
        # 错误日志处理器
        error_log_file = os.path.join(self.log_dir, "error.log")
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 额外参数
        """
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 额外参数
        """
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 额外参数
        """
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            exc_info: 是否包含异常信息
            **kwargs: 额外参数
        """
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """记录严重错误日志
        
        Args:
            message: 日志消息
            exc_info: 是否包含异常信息
            **kwargs: 额外参数
        """
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        """记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外参数
        """
        # 检查是否启用调试模式
        if level == logging.DEBUG and not self.config_manager.is_debug_mode():
            return
        
        # 格式化消息
        formatted_message = self._format_message(message, **kwargs)
        
        # 记录日志
        if kwargs.get("exc_info"):
            self.logger.log(level, formatted_message, exc_info=True)
        else:
            self.logger.log(level, formatted_message)
    
    def _format_message(self, message: str, **kwargs) -> str:
        """格式化日志消息
        
        Args:
            message: 原始消息
            **kwargs: 额外参数
            
        Returns:
            格式化后的消息
        """
        # 移除exc_info参数
        kwargs.pop("exc_info", None)
        
        # 如果没有额外参数，直接返回消息
        if not kwargs:
            return message
        
        # 格式化额外参数
        extra_info = []
        for key, value in kwargs.items():
            if isinstance(value, (dict, list)):
                value = str(value)
            extra_info.append(f"{key}={value}")
        
        # 组合消息
        return f"{message} | {' | '.join(extra_info)}"
    
    def log_exception(self, message: str, exc: Exception) -> None:
        """记录异常日志
        
        Args:
            message: 日志消息
            exc: 异常对象
        """
        self.error(
            f"{message}: {str(exc)}",
            exc_info=True,
            exception_type=exc.__class__.__name__
        )
    
    def log_api_call(self, api_name: str, method: str, url: str, **kwargs) -> None:
        """记录API调用日志
        
        Args:
            api_name: API名称
            method: 请求方法
            url: 请求URL
            **kwargs: 额外参数
        """
        self.info(
            f"API调用: {api_name}",
            method=method,
            url=url,
            **kwargs
        )
    
    def log_api_response(self, api_name: str, status_code: int, **kwargs) -> None:
        """记录API响应日志
        
        Args:
            api_name: API名称
            status_code: 状态码
            **kwargs: 额外参数
        """
        if status_code >= 400:
            self.error(
                f"API响应错误: {api_name}",
                status_code=status_code,
                **kwargs
            )
        else:
            self.info(
                f"API响应成功: {api_name}",
                status_code=status_code,
                **kwargs
            )
    
    def log_memory_operation(self, operation: str, memory_type: str, **kwargs) -> None:
        """记录记忆操作日志
        
        Args:
            operation: 操作类型
            memory_type: 记忆类型
            **kwargs: 额外参数
        """
        self.debug(
            f"记忆操作: {operation}",
            memory_type=memory_type,
            **kwargs
        )
    
    def log_config_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """记录配置变更日志
        
        Args:
            key: 配置键
            old_value: 旧值
            new_value: 新值
        """
        self.info(
            "配置变更",
            key=key,
            old_value=old_value,
            new_value=new_value
        )
    
    def log_user_action(self, action: str, **kwargs) -> None:
        """记录用户操作日志
        
        Args:
            action: 操作类型
            **kwargs: 额外参数
        """
        self.info(
            f"用户操作: {action}",
            **kwargs
        )
    
    def get_log_files(self) -> Dict[str, str]:
        """获取日志文件路径
        
        Returns:
            日志文件路径字典
        """
        return {
            "main": os.path.join(self.log_dir, "ganaterm.log"),
            "error": os.path.join(self.log_dir, "error.log")
        }
    
    def clear_logs(self) -> None:
        """清除日志文件"""
        for log_file in self.get_log_files().values():
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("")
                self.info(f"已清除日志文件: {log_file}")
            except Exception as e:
                self.error(f"清除日志文件失败: {log_file}", exc_info=True)
    
    def rotate_logs(self) -> None:
        """轮转日志文件"""
        for handler in self.logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.doRollover()
        self.info("已轮转日志文件")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息
        
        Returns:
            日志统计信息字典
        """
        stats = {}
        for name, path in self.get_log_files().items():
            try:
                size = os.path.getsize(path)
                stats[name] = {
                    "size": size,
                    "size_formatted": self._format_size(size),
                    "last_modified": datetime.fromtimestamp(
                        os.path.getmtime(path)
                    ).strftime("%Y-%m-%d %H:%M:%S")
                }
            except Exception as e:
                self.error(f"获取日志统计信息失败: {name}", exc_info=True)
        return stats
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小
        
        Args:
            size: 文件大小（字节）
            
        Returns:
            格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f}{unit}"
            size /= 1024
        return f"{size:.2f}TB" 