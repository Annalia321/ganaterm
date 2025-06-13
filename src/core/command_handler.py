#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令处理器 - 处理用户输入的命令
"""

import os
import sys
import shlex
from typing import Optional, List, Dict, Any, Union, Callable
from datetime import datetime

class CommandHandler:
    """命令处理器，处理用户输入的命令"""
    
    def __init__(
        self,
        config_manager: Any,
        logger: Any,
        model_manager: Any,
        memory_manager: Any,
        ui_manager: Any
    ):
        """初始化命令处理器
        
        Args:
            config_manager: 配置管理器实例
            logger: 日志管理器实例
            model_manager: 模型管理器实例
            memory_manager: 记忆管理器实例
            ui_manager: UI管理器实例
        """
        self.config_manager = config_manager
        self.logger = logger
        self.model_manager = model_manager
        self.memory_manager = memory_manager
        self.ui_manager = ui_manager
        
        # 初始化命令映射
        self.commands = self._init_commands()
    
    def _init_commands(self) -> Dict[str, Callable]:
        """初始化命令映射
        
        Returns:
            命令映射字典
        """
        return {
            "help": self._handle_help,
            "model": self._handle_model,
            "memory": self._handle_memory,
            "config": self._handle_config,
            "exit": self._handle_exit
        }
    
    def handle_command(self, command: str) -> bool:
        """处理命令
        
        Args:
            command: 命令字符串
            
        Returns:
            是否继续运行
        """
        # 记录用户操作
        self.logger.log_user_action("command", command=command)
        
        # 解析命令
        try:
            parts = shlex.split(command)
            if not parts:
                return True
            
            # 处理特殊命令
            if parts[0].startswith("/"):
                cmd = parts[0][1:].lower()
                args = parts[1:]
                
                if cmd in self.commands:
                    return self.commands[cmd](args)
                else:
                    self.ui_manager.print_error(f"未知命令: {cmd}")
                    return True
            
            # 处理普通对话
            return self._handle_chat(command)
            
        except Exception as e:
            self.logger.error("命令处理失败", exc_info=True)
            self.ui_manager.print_error(f"命令处理失败: {str(e)}")
            return True
    
    def _handle_help(self, args: List[str]) -> bool:
        """处理帮助命令
        
        Args:
            args: 命令参数
            
        Returns:
            是否继续运行
        """
        self.ui_manager.print_help()
        return True
    
    def _handle_model(self, args: List[str]) -> bool:
        """处理模型命令
        
        Args:
            args: 命令参数
            
        Returns:
            是否继续运行
        """
        if not args:
            self.ui_manager.print_error("缺少子命令")
            return True
        
        subcmd = args[0].lower()
        subargs = args[1:]
        
        if subcmd == "list":
            # 列出可用模型
            models = self.model_manager.get_available_models()
            self.ui_manager.print_table("可用模型", [
                {"模型": model} for model in models
            ])
            
        elif subcmd == "switch":
            # 切换模型
            if not subargs:
                self.ui_manager.print_error("缺少模型名称")
                return True
            
            model_name = subargs[0]
            if self.model_manager.set_current_model(model_name):
                self.ui_manager.print_success(f"已切换到模型: {model_name}")
            else:
                self.ui_manager.print_error(f"切换模型失败: {model_name}")
            
        elif subcmd == "info":
            # 显示模型信息
            model_info = self.model_manager.get_model_info(
                self.model_manager.get_current_model()
            )
            if model_info:
                self.ui_manager.print_model_info(model_info)
            else:
                self.ui_manager.print_error("获取模型信息失败")
            
        else:
            self.ui_manager.print_error(f"未知子命令: {subcmd}")
        
        return True
    
    def _handle_memory(self, args: List[str]) -> bool:
        """处理记忆命令
        
        Args:
            args: 命令参数
            
        Returns:
            是否继续运行
        """
        if not args:
            self.ui_manager.print_error("缺少子命令")
            return True
        
        subcmd = args[0].lower()
        subargs = args[1:]
        
        if subcmd == "add":
            # 添加记忆
            if not subargs:
                self.ui_manager.print_error("缺少记忆内容")
                return True
            
            content = " ".join(subargs)
            try:
                self.memory_manager.add_memory(content)
                self.ui_manager.print_success("记忆添加成功")
            except Exception as e:
                self.ui_manager.print_error(f"记忆添加失败: {str(e)}")
            
        elif subcmd == "search":
            # 搜索记忆
            if not subargs:
                self.ui_manager.print_error("缺少搜索关键词")
                return True
            
            keyword = " ".join(subargs)
            try:
                memories = self.memory_manager.search_memories(keyword)
                self.ui_manager.print_memory_list(memories)
            except Exception as e:
                self.ui_manager.print_error(f"记忆搜索失败: {str(e)}")
            
        elif subcmd == "list":
            # 列出记忆
            try:
                memories = self.memory_manager.get_all_memories()
                self.ui_manager.print_memory_list(memories)
            except Exception as e:
                self.ui_manager.print_error(f"获取记忆列表失败: {str(e)}")
            
        elif subcmd == "clear":
            # 清除记忆
            try:
                self.memory_manager.clear_memories()
                self.ui_manager.print_success("记忆清除成功")
            except Exception as e:
                self.ui_manager.print_error(f"记忆清除失败: {str(e)}")
            
        else:
            self.ui_manager.print_error(f"未知子命令: {subcmd}")
        
        return True
    
    def _handle_config(self, args: List[str]) -> bool:
        """处理配置命令
        
        Args:
            args: 命令参数
            
        Returns:
            是否继续运行
        """
        if not args:
            self.ui_manager.print_error("缺少子命令")
            return True
        
        subcmd = args[0].lower()
        subargs = args[1:]
        
        if subcmd == "show":
            # 显示配置
            config = self.config_manager.get_all_config()
            self.ui_manager.print_config(config)
            
        elif subcmd == "set":
            # 设置配置
            if len(subargs) < 2:
                self.ui_manager.print_error("缺少配置键值")
                return True
            
            key = subargs[0]
            value = " ".join(subargs[1:])
            try:
                self.config_manager.set_config(key, value)
                self.ui_manager.print_success(f"配置设置成功: {key}={value}")
            except Exception as e:
                self.ui_manager.print_error(f"配置设置失败: {str(e)}")
            
        elif subcmd == "reset":
            # 重置配置
            try:
                self.config_manager.reset_config()
                self.ui_manager.print_success("配置重置成功")
            except Exception as e:
                self.ui_manager.print_error(f"配置重置失败: {str(e)}")
            
        else:
            self.ui_manager.print_error(f"未知子命令: {subcmd}")
        
        return True
    
    def _handle_exit(self, args: List[str]) -> bool:
        """处理退出命令
        
        Args:
            args: 命令参数
            
        Returns:
            是否继续运行
        """
        self.ui_manager.print_info("正在退出...")
        return False
    
    def _handle_chat(self, message: str) -> bool:
        """处理聊天消息
        
        Args:
            message: 聊天消息
            
        Returns:
            是否继续运行
        """
        try:
            # 获取相关记忆
            memories = self.memory_manager.search_memories(message)
            
            # 构建消息列表
            messages = []
            
            # 添加系统提示
            messages.append({
                "role": "system",
                "content": "你是一个智能终端AI助手，可以帮助用户完成各种任务。"
            })
            
            # 添加相关记忆
            if memories:
                memory_context = "\n".join([
                    f"- {m['content']}" for m in memories
                ])
                messages.append({
                    "role": "system",
                    "content": f"相关记忆:\n{memory_context}"
                })
            
            # 添加用户消息
            messages.append({
                "role": "user",
                "content": message
            })
            
            # 显示进度
            self.ui_manager.print_progress("正在思考...")
            
            # 发送请求
            response = self.model_manager.chat(messages)
            
            # 显示响应
            if response["success"]:
                self.ui_manager.print_markdown(response["content"])
                
                # 添加记忆
                self.memory_manager.add_memory(
                    f"用户: {message}\n助手: {response['content']}"
                )
            else:
                self.ui_manager.print_error("获取响应失败")
            
        except Exception as e:
            self.logger.error("聊天处理失败", exc_info=True)
            self.ui_manager.print_error(f"聊天处理失败: {str(e)}")
        
        return True 