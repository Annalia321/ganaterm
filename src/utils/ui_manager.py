#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI管理器 - 处理终端界面显示相关的功能
"""

import os
import sys
import time
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

class UIManager:
    """UI管理器，处理终端界面显示相关的功能"""
    
    def __init__(self, config_manager: Any, logger: Any):
        """初始化UI管理器
        
        Args:
            config_manager: 配置管理器实例
            logger: 日志管理器实例
        """
        self.config_manager = config_manager
        self.logger = logger
        
        # 初始化控制台
        self.console = Console()
        
        # 初始化提示会话
        self.session = PromptSession(
            history=FileHistory(
                os.path.join(
                    self.config_manager.get_data_dir(),
                    "history.txt"
                )
            )
        )
        
        # 初始化样式
        self.style = Style.from_dict({
            "prompt": "ansicyan bold",
            "input": "ansigreen",
            "output": "ansiyellow",
            "error": "ansired bold",
            "info": "ansiblue",
            "success": "ansigreen",
            "warning": "ansiyellow bold"
        })
    
    def print_welcome(self) -> None:
        """打印欢迎信息"""
        welcome_text = """
        [bold cyan]欢迎使用 Ganaterm![/bold cyan]
        
        这是一个智能终端AI助手，支持多种LLM模型，具有记忆功能和上下文理解能力。
        
        基本命令:
        - 输入问题直接对话
        - /help 显示帮助信息
        - /model 切换模型
        - /memory 管理记忆
        - /config 查看配置
        - /exit 退出程序
        
        记忆命令:
        - /memory add 添加记忆
        - /memory search 搜索记忆
        - /memory list 列出记忆
        - /memory clear 清除记忆
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="[bold cyan]Ganaterm[/bold cyan]",
            border_style="cyan"
        ))
    
    def print_help(self) -> None:
        """打印帮助信息"""
        help_text = """
        [bold]命令列表:[/bold]
        
        [cyan]基本命令[/cyan]
        /help - 显示帮助信息
        /model - 切换模型
        /memory - 管理记忆
        /config - 查看配置
        /exit - 退出程序
        
        [cyan]记忆命令[/cyan]
        /memory add <内容> - 添加记忆
        /memory search <关键词> - 搜索记忆
        /memory list - 列出记忆
        /memory clear - 清除记忆
        
        [cyan]配置命令[/cyan]
        /config show - 显示配置
        /config set <键> <值> - 设置配置
        /config reset - 重置配置
        
        [cyan]模型命令[/cyan]
        /model list - 列出可用模型
        /model switch <模型名> - 切换模型
        /model info - 显示模型信息
        """
        
        self.console.print(Panel(
            Markdown(help_text),
            title="[bold cyan]帮助信息[/bold cyan]",
            border_style="cyan"
        ))
    
    def print_error(self, message: str) -> None:
        """打印错误信息
        
        Args:
            message: 错误消息
        """
        self.console.print(f"[bold red]错误:[/bold red] {message}")
    
    def print_info(self, message: str) -> None:
        """打印信息
        
        Args:
            message: 信息消息
        """
        self.console.print(f"[bold blue]信息:[/bold blue] {message}")
    
    def print_success(self, message: str) -> None:
        """打印成功信息
        
        Args:
            message: 成功消息
        """
        self.console.print(f"[bold green]成功:[/bold green] {message}")
    
    def print_warning(self, message: str) -> None:
        """打印警告信息
        
        Args:
            message: 警告消息
        """
        self.console.print(f"[bold yellow]警告:[/bold yellow] {message}")
    
    def print_model_info(self, model_info: Dict[str, Any]) -> None:
        """打印模型信息
        
        Args:
            model_info: 模型信息字典
        """
        table = Table(title="模型信息")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="green")
        
        for key, value in model_info.items():
            if isinstance(value, (dict, list)):
                value = str(value)
            table.add_row(key, value)
        
        self.console.print(table)
    
    def print_memory_list(self, memories: List[Dict[str, Any]]) -> None:
        """打印记忆列表
        
        Args:
            memories: 记忆列表
        """
        if not memories:
            self.print_info("没有找到记忆")
            return
        
        table = Table(title="记忆列表")
        table.add_column("ID", style="cyan")
        table.add_column("类型", style="green")
        table.add_column("内容", style="yellow")
        table.add_column("时间", style="blue")
        table.add_column("重要性", style="magenta")
        
        for memory in memories:
            table.add_row(
                memory["id"],
                memory["type"],
                memory["content"],
                memory["timestamp"],
                str(memory["importance"])
            )
        
        self.console.print(table)
    
    def print_config(self, config: Dict[str, Any]) -> None:
        """打印配置信息
        
        Args:
            config: 配置字典
        """
        table = Table(title="配置信息")
        table.add_column("键", style="cyan")
        table.add_column("值", style="green")
        
        for key, value in config.items():
            if isinstance(value, (dict, list)):
                value = str(value)
            table.add_row(key, value)
        
        self.console.print(table)
    
    def print_progress(self, message: str) -> None:
        """打印进度信息
        
        Args:
            message: 进度消息
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            progress.add_task(message, total=None)
            time.sleep(0.1)
    
    def print_stream(self, content: str) -> None:
        """打印流式内容
        
        Args:
            content: 内容
        """
        self.console.print(content, end="")
        sys.stdout.flush()
    
    def print_markdown(self, content: str) -> None:
        """打印Markdown内容
        
        Args:
            content: Markdown内容
        """
        self.console.print(Markdown(content))
    
    def print_table(self, title: str, data: List[Dict[str, Any]]) -> None:
        """打印表格
        
        Args:
            title: 表格标题
            data: 表格数据
        """
        if not data:
            self.print_info("没有数据")
            return
        
        table = Table(title=title)
        
        # 添加列
        for key in data[0].keys():
            table.add_column(key, style="cyan")
        
        # 添加行
        for row in data:
            table.add_row(*[str(value) for value in row.values()])
        
        self.console.print(table)
    
    def print_panel(self, content: str, title: Optional[str] = None) -> None:
        """打印面板
        
        Args:
            content: 面板内容
            title: 面板标题
        """
        self.console.print(Panel(
            content,
            title=title,
            border_style="cyan"
        ))
    
    def get_input(self, prompt: str = "> ") -> str:
        """获取用户输入
        
        Args:
            prompt: 提示文本
            
        Returns:
            用户输入
        """
        return self.session.prompt(
            HTML(f"<prompt>{prompt}</prompt>"),
            style=self.style
        )
    
    def clear_screen(self) -> None:
        """清屏"""
        os.system("clear" if os.name == "posix" else "cls")
    
    def print_separator(self, char: str = "=", length: int = 80) -> None:
        """打印分隔线
        
        Args:
            char: 分隔字符
            length: 分隔线长度
        """
        self.console.print(char * length)
    
    def print_timestamp(self) -> None:
        """打印时间戳"""
        self.console.print(
            f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )
    
    def print_model_status(self, model_name: str, status: bool) -> None:
        """打印模型状态
        
        Args:
            model_name: 模型名称
            status: 状态
        """
        status_text = "[green]可用[/green]" if status else "[red]不可用[/red]"
        self.console.print(f"模型 {model_name}: {status_text}")
    
    def print_usage_stats(self, usage: Dict[str, Any]) -> None:
        """打印使用统计
        
        Args:
            usage: 使用统计字典
        """
        table = Table(title="使用统计")
        table.add_column("模型", style="cyan")
        table.add_column("总请求数", style="green")
        table.add_column("总token数", style="yellow")
        table.add_column("总费用", style="magenta")
        
        for model, stats in usage.items():
            table.add_row(
                model,
                str(stats.get("total_requests", 0)),
                str(stats.get("total_tokens", 0)),
                f"${stats.get('total_cost', 0):.4f}"
            )
        
        self.console.print(table)
    
    def print_capabilities(self, capabilities: Dict[str, List[str]]) -> None:
        """打印模型能力
        
        Args:
            capabilities: 能力字典
        """
        for model, caps in capabilities.items():
            self.console.print(f"\n[bold cyan]{model}[/bold cyan]")
            for cap in caps:
                self.console.print(f"  • {cap}")
    
    def print_memory_stats(self, stats: Dict[str, Any]) -> None:
        """打印记忆统计
        
        Args:
            stats: 统计字典
        """
        table = Table(title="记忆统计")
        table.add_column("类型", style="cyan")
        table.add_column("数量", style="green")
        table.add_column("大小", style="yellow")
        table.add_column("最后更新", style="blue")
        
        for type_, data in stats.items():
            table.add_row(
                type_,
                str(data["count"]),
                data["size"],
                data["last_updated"]
            )
        
        self.console.print(table)
    
    def print_log_stats(self, stats: Dict[str, Any]) -> None:
        """打印日志统计
        
        Args:
            stats: 统计字典
        """
        table = Table(title="日志统计")
        table.add_column("文件", style="cyan")
        table.add_column("大小", style="green")
        table.add_column("最后修改", style="yellow")
        
        for name, data in stats.items():
            table.add_row(
                name,
                data["size_formatted"],
                data["last_modified"]
            )
        
        self.console.print(table) 