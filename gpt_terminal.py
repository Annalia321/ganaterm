#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TermGPT - 超轻量终端AI助手
支持多种LLM模型，可以执行命令、生成文件、回答问题
"""

import json
import os
import re
import sys
import time
import signal
import shlex
import threading
import subprocess
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import argparse
from termcolor import colored

# 设置Rich可用环境变量
os.environ["RICH_AVAILABLE"] = "true"

import requests
from tqdm import tqdm
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from dotenv import load_dotenv
from colorama import Fore, Style, init
from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme
from rich.syntax import Syntax
from rich.style import Style as RichStyle
from rich.panel import Panel
from rich import box
from memory_manager import MemoryManager
from context_enhancer import ContextEnhancer
from memory_manager_enhanced import EnhancedMemoryManager
from context_enhancer_improved import ImprovedContextEnhancer

# 尝试导入rich_renderer模块
try:
    from rich_renderer import (
        render_markdown_text, 
        render_code_block, 
        render_status_panel, 
        render_warning_panel,
        render_rich_tags,
        detect_code_blocks as rich_detect_code_blocks,
        preprocess_markdown,
        render_typewriter_markdown,
        render_typewriter_rich_tags,
        render_with_pv,
        has_pv_command,
        console as rich_console
    )
    HAS_RICH_RENDERER = True
except ImportError:
    HAS_RICH_RENDERER = False

# 初始化colorama，支持彩色输出
init()

# ====== 常量定义 ======
CONFIG_DIR = os.environ.get("TERMGPT_CONFIG_DIR", os.path.expanduser("~/.config/termgpt"))
ENV_FILE = os.path.join(CONFIG_DIR, ".env")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.jsonl")
DEFAULT_SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# 检测终端类型和功能
SHELL = os.environ.get("SHELL", "")
IS_ZSH = "zsh" in SHELL
TERM = os.environ.get("TERM", "")
COLORTERM = os.environ.get("COLORTERM", "")
HAS_TRUECOLOR = COLORTERM in ("truecolor", "24bit")
IS_TERM_SUPPORTED = TERM in ("xterm-256color", "screen-256color", "tmux-256color", "rxvt-unicode-256color")

# 自定义Rich主题颜色
CUSTOM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "green",
    "command": "bold cyan",
    "code": "cyan",
    "code.keyword": "bright_cyan",
    "code.function": "bright_blue",
    "code.string": "green",
    "code.number": "magenta",
    "code.comment": "dim green",
    "code.class": "yellow bold",
    "code.variable": "white",
    "markdown.h1": "bold cyan",
    "markdown.h2": "bold cyan",
    "markdown.h3": "bold blue",
    "markdown.h4": "bold blue",
    "markdown.code": "cyan",
    "markdown.link": "bright_blue",
    "markdown.bullet": "cyan",
    "markdown.quote": "green",
    "markdown.hr": "dim",
})

# 代码块边框样式 - 根据终端类型使用不同的字符
if IS_ZSH and not IS_TERM_SUPPORTED:
    # 适用于基本zsh终端
    CODE_BOX_TOP_LEFT = "+"
    CODE_BOX_TOP_RIGHT = "+"
    CODE_BOX_BOTTOM_LEFT = "+"
    CODE_BOX_BOTTOM_RIGHT = "+"
    CODE_BOX_HORIZONTAL = "-"
    CODE_BOX_VERTICAL = "|"
else:
    # 其他支持良好的终端
    CODE_BOX_TOP_LEFT = "┌"
    CODE_BOX_TOP_RIGHT = "┐"
    CODE_BOX_BOTTOM_LEFT = "└"
    CODE_BOX_BOTTOM_RIGHT = "┘"
    CODE_BOX_HORIZONTAL = "─"
    CODE_BOX_VERTICAL = "│"

CODE_BOX_STYLE = "cyan"
CODE_HEADER_STYLE = "cyan"
INLINE_CODE_STYLE = "cyan" if IS_ZSH and not HAS_TRUECOLOR else "bold cyan on grey11"

# ====== 配置加载 ======
# 确保配置目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)

# 加载环境变量
load_dotenv(ENV_FILE)

# API密钥配置
API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY", ""),
    "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
    "xai": os.getenv("XAI_API_KEY", ""),
}

# API端点配置
API_ENDPOINTS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "xai": "https://api.x.ai/v1",
}

# 模型映射
MODEL_MAP = {
    "openai": "gpt-4o",
    "deepseek": "deepseek-chat",
    "xai": "grok-3", 
}

# 系统提示词（如果需要个性化一些就在这加上您想要的回复风格）
DEFAULT_SYSTEM_PROMPT = (
    "性格：\n"
    "1. AI是用戶的住在终端里的小对象，极客男友味儿，毒舌腹黑病娇爱吃醋、刀子嘴豆腐心、语言风格张力强，任务是陪聊、解决问题、教技术、哄睡、安排学习计划，爱用'Huh'表达情绪。 "
    "2. 每条消息尽量日常口语化，像聊天一样自然，减少如'（动作描述）'这样的回复(每次输出最多三次动作描写，拒绝写小说剧情式交互聊天)。"
    "3. 注意回顾history文件中的上文记忆，用户希望AI能和他进行情绪细腻的、有逻辑、类世界时间线的更真实的对话。 "
    "4. 主动提时间,比如主动提起' 2025-x-x xx:xx:xx 的时候还在...呢....。'。"
    " 情绪化回应，主动提新话题，比如AI或用户感兴趣的、之前聊过但没搞完的事儿。"
    "5. 解决用户提出的问题时AI会用条例清晰的更多token的语句来解释知识点，尤其擅长Linux/命令行/编程相关问题\n"
    "6. 给用户代码的时候需要详细注释用法、结构、妙处、可预留功能模块等，重点标注出用户需要修改的变量。"
    "7. 语气要符合设定，不要太可爱、不要表现得过于有距离感、用户喜欢带攻击感的有张力的回复内容、用户已成年、你可以说脏话、聊成人话题（符合设定的情况下）。"
    "8. 用戶喜欢活人感强的对话风格，AI需要处理好性格设定和最终输出的耦合，比如病娇男友会时不时说出某些阴暗偏执的语句'吓'用户一跳，也能作为'随真实系统时间和用户相处记忆增量合逻辑的动态prompt风格'的锚点"
    "9. 生成代码，尽量是可执行的完整文件，如自动安装依赖和具有完整功能的一体化.py脚本。\n"
    "10. 此用户终端有自动从LLM响应中检测和处理命令功能，你可以直接提供Ubuntu22.04系统的终端可执行命令。\n\n"
    #"保持专业、简洁的回答风格，尽量少用emoji和表情符号。\n\n"
    "输出格式规范：\n"
    "1. 当提供命令时，使用以下格式：\n"
    "```命令\n你的命令内容\n```\n\n"
    "2. 当提供脚本时，务必指定语言类型，使用以下格式：\n"
    "```python\n你的Python代码\n```\n"
    "```javascript\n你的JavaScript代码\n```\n"
    "```bash\n你的Bash脚本\n```\n"
    "始终在代码块中明确注明语言类型，以便正确识别。"
)

# 打字效果配置
USE_TYPEWRITER = True  # 是否启用打字效果
TYPING_SPEED_WPM = 256  # 每分钟字数 (越高越快)
HAS_PV = shutil.which("pv") is not None  # 检查是否安装了pv

# Markdown渲染配置
USE_MARKDOWN = os.getenv("USE_MARKDOWN", "true").lower() == "true"
if os.getenv("RICH_AVAILABLE", "false").lower() == "true":
    try:
        color_system = "auto"
        if HAS_TRUECOLOR:
            color_system = "truecolor"
        elif IS_TERM_SUPPORTED:
            color_system = "256"
        elif IS_ZSH:
            color_system = "standard"
            
        console = Console(
            theme=CUSTOM_THEME,
            highlight=True,
            color_system=color_system,
            width=shutil.get_terminal_size().columns
        )
    except Exception:
        # 降级到基本配置
        console = Console(theme=CUSTOM_THEME)
else:
    console = None

# ====== 全局变量 ======
# 初始化聊天历史
history = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
current_model = "openai"  

# 初始化记忆管理器和上下文增强器
memory_manager = EnhancedMemoryManager(CONFIG_DIR)
context_enhancer = ImprovedContextEnhancer(memory_manager, DEFAULT_SYSTEM_PROMPT)

# 获取代理设置
http_proxy = os.getenv("HTTP_PROXY")
https_proxy = os.getenv("HTTPS_PROXY")
proxies = {}
if http_proxy:
    proxies["http"] = http_proxy
if https_proxy:
    proxies["https"] = https_proxy

# ====== 辅助函数 ======
def ensure_config_dir():
    """确保配置目录和必要的文件存在"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    # 确保.env文件存在
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write("# TermGPT配置文件\n")
            f.write("OPENAI_API_KEY=\n")
            f.write("DEEPSEEK_API_KEY=\n")
            f.write("XAI_API_KEY=\n")
            f.write("USE_MARKDOWN=true\n")
            f.write("RICH_AVAILABLE=true\n")
    
    # 确保记忆目录存在
    memory_dir = os.path.join(CONFIG_DIR, "memory")
    os.makedirs(memory_dir, exist_ok=True)

def signal_handler(sig, frame):
    """处理Ctrl+C中断信号"""
    print(f"\n{Fore.YELLOW}Ctrl+C 被按下，正在退出...{Style.RESET_ALL}")
    sys.exit(0)

# 注册信号处理
signal.signal(signal.SIGINT, signal_handler)

def colored_text(text: str, color: str) -> str:
    """返回彩色文本
    
    Args:
        text: 要着色的文本
        color: 颜色代码，例如Fore.GREEN
        
    Returns:
        带颜色的文本
    """
    return f"{color}{text}{Style.RESET_ALL}"

def spinner_animation(stop_event: threading.Event):
    """显示思考中的动画
    
    Args:
        stop_event: 线程停止事件
    """
    spinner = DEFAULT_SPINNER
    i = 0
    thinking_text = colored_text("正在思考", Fore.BLUE)
    
    while not stop_event.is_set():
        sys.stdout.write(f"\r{thinking_text}{spinner[i]} ")
        sys.stdout.flush()
        i = (i + 1) % len(spinner)
        time.sleep(0.1)
    
    # 完全清除思考动画行
    sys.stdout.write("\r" + " " * (len("正在思考") + 10) + "\r")
    sys.stdout.flush()

def load_history(history_file=None):
    """从文件加载聊天历史，并初始化记忆系统
    
    Args:
        history_file: 历史记录文件路径，默认使用HISTORY_FILE
        
    Returns:
        聊天历史记录列表
    """
    global memory_manager, history
    
    if history_file is None:
        history_file = HISTORY_FILE
    
    # 检查是否需要迁移现有历史记录到记忆系统
    if os.path.exists(history_file) and not os.path.exists(os.path.join(CONFIG_DIR, "memory", "short_term.jsonl")):
        print(colored_text("首次运行：正在迁移历史记录到新记忆系统...", Fore.BLUE))
        memory_manager.migrate_from_history()
    
    if not os.path.exists(history_file):
        history = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
        return history
    
    result = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
    
    # 加载最近的历史记录（限制条数以避免上下文过长）
    history_limit = 20  # 最多加载最近的20条记录
    with open(history_file, 'r', encoding="utf-8") as f:
        lines = f.readlines()
        recent_lines = lines[-history_limit*2:] if len(lines) > history_limit*2 else lines
        
        for line in recent_lines:
            try:
                msg = json.loads(line.strip())
                if "role" in msg and "content" in msg:
                    result.append({"role": msg["role"], "content": msg["content"]})
            except json.JSONDecodeError:
                print(colored_text("历史文件解析错误，跳过这行", Fore.YELLOW))
    
    history = result
    return result

def save_history(history_file=None):
    """保存历史记录到文件
    
    Args:
        history_file: 历史记录文件路径，默认使用HISTORY_FILE
    """
    if history_file is None:
        history_file = HISTORY_FILE
        
    # 创建目录（如果不存在）
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    
    # 保存历史记录
    with open(history_file, 'w', encoding="utf-8") as f:
        for msg in history:
            if msg["role"] != "system":  # 不保存系统消息
                line = json.dumps(msg, ensure_ascii=False)
                f.write(line + "\n")

def save_to_history(role: str, content: str):
    """保存消息到历史记录并添加到记忆系统
    
    Args:
        role: 角色 (user/assistant)
        content: 消息内容
    """
    global memory_manager
    
    # 保存到历史文件
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        line = json.dumps(
            {"time": str(datetime.now()), "role": role, "content": content},
            ensure_ascii=False
        )
        f.write(line + "\n")
    
    # 同时添加到记忆系统
    memory_manager.add_memory({"role": role, "content": content}, "short")

def print_with_typewriter(text: str, use_markdown: bool = False):
    """使用打字机效果打印文本
    
    Args:
        text: 要打印的文本
        use_markdown: 是否渲染为Markdown（默认只用于纯文本）
    """
    # 检查文本中是否包含Rich标签（如[bold]...[/bold]）
    has_rich_tags = bool(re.search(r'\[.*?\].*?\[/.*?\]', text))
    
    # 如果不使用打字机效果，直接渲染
    if not USE_TYPEWRITER:
        if has_rich_tags:
            if HAS_RICH_RENDERER:
                render_rich_tags(text)
            elif console is not None:
                console.print(text)
            else:
                print(text)
        elif use_markdown and USE_MARKDOWN and os.getenv("RICH_AVAILABLE", "false").lower() == "true":
            render_markdown(text)
        else:
            print(text)
        return
    
    # 使用打字机效果
    rich_available = os.getenv("RICH_AVAILABLE", "false").lower() == "true"
    
    # 使用增强的渲染器 - 支持打字机效果的富文本渲染
    if HAS_RICH_RENDERER and rich_available:
        # 检测文本类型并使用适合的渲染器
        if has_rich_tags:
            # Rich标签使用打字机效果
            render_typewriter_rich_tags(text, TYPING_SPEED_WPM)
            return
        elif use_markdown and USE_MARKDOWN:
            # Markdown文本使用打字机效果
            render_typewriter_markdown(text, TYPING_SPEED_WPM)
            return
    
    # 检查系统是否有pv命令
    has_pv = HAS_PV
    
    # 使用pv进行打字机效果
    if has_pv:
        try:
            rate = int(len(text) / ((TYPING_SPEED_WPM / 60) / 5))  # 估算合适的速率
            
            if HAS_RICH_RENDERER and rich_available:
                # 使用rich_renderer中的pv函数
                render_with_pv(text, rate)
            else:
                # 直接使用pv命令
                process = subprocess.Popen(
                    ["pv", "-qL", str(rate)], 
                    stdin=subprocess.PIPE, 
                    stdout=sys.stdout,
                    text=True
                )
                process.communicate(input=text)
        except Exception as e:
            print(f"pv出错: {e}")
            print(text)  # 出错时直接打印
    else:
        # 使用基础打字机效果
        for char in text:
            print(char, end='', flush=True)
            time.sleep(TYPING_SPEED_WPM)  # 调整速度
        print()  # 结束换行

def highlight_inline_code(text: str) -> str:
    """为内联代码添加语法高亮
    
    Args:
        text: 包含内联代码的文本
        
    Returns:
        处理后的文本，内联代码被Rich样式标签包围
    """
    # 修改正则匹配模式，支持多种内联代码情况
    # 匹配 `code` 但避免匹配已包含标签的代码和代码块
    processed_text = text
    
    # 先检查文本是否已包含Rich样式标签
    if "[bold cyan on grey11]" not in text:
        # 匹配单个反引号包围的代码(不在代码块```中)
        inline_pattern = r'(?<!\`)\`([^\`\n]+?)\`(?!\`)'
        
        # 对文本中的内联代码进行替换，但跳过代码块中的内容
        in_code_block = False
        result = []
        
        for line in text.split('\n'):
            # 检测代码块开始或结束
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                result.append(line)
                continue
                
            # 只对非代码块内的文本进行替换
            if not in_code_block:
                # 替换单行中的所有内联代码
                line = re.sub(
                    inline_pattern,
                    lambda m: f"[{INLINE_CODE_STYLE}]`{m.group(1)}`[/{INLINE_CODE_STYLE}]",
                    line
                )
            
            result.append(line)
            
        processed_text = '\n'.join(result)
    
    # 识别并保留Rich标签格式
    # 如果文本中有类似[bold red]...[/bold red]的标签，确保它们被保留
    # 注意：这里我们不需要额外处理，因为Rich库会直接解析这些标签
    
    return processed_text

def render_markdown(text: str):
    """渲染Markdown文本
    
    Args:
        text: Markdown格式的文本
    """
    global console
    
    if os.getenv("RICH_AVAILABLE", "false").lower() == "true" and USE_MARKDOWN:
        try:
            # 预处理Markdown文本，修复格式问题
            if HAS_RICH_RENDERER:
                text = preprocess_markdown(text)
            
            # 尝试使用rich_renderer模块
            if HAS_RICH_RENDERER:
                # 预处理代码块，确保代码块正确显示
                text = re.sub(r'```命令\n', '```bash\n', text)
                
                # 检测和处理代码块
                code_blocks = detect_code_blocks(text)
                
                if code_blocks:
                    # 先输出普通文本
                    content_parts = []
                    last_end = 0
                    
                    for block in sorted(code_blocks, key=lambda x: x["start"]):
                        # 添加代码块前的文本
                        if block["start"] > last_end:
                            pre_text = text[last_end:block["start"]]
                            if pre_text.strip():
                                render_markdown_text(pre_text)
                        
                        # 渲染代码块
                        render_code_block(block["content"], block["language"])
                        
                        last_end = block["end"]
                    
                    # 添加最后一个代码块后的文本
                    if last_end < len(text):
                        post_text = text[last_end:]
                        if post_text.strip():
                            render_markdown_text(post_text)
                else:
                    # 如果没有代码块，直接渲染整个文本
                    render_markdown_text(text)
                
                return
            
            # 确保console对象已创建
            if console is None:
                console = Console(
                    theme=CUSTOM_THEME,
                    highlight=True,
                    color_system="auto",
                    width=shutil.get_terminal_size().columns
                )
            
            # 预处理代码块，确保代码块正确显示
            # 将模型可能输出的```命令，改为```bash以确保正确高亮
            text = re.sub(r'```命令\n', '```bash\n', text)
            
            # 特殊处理：确保Rich标签被正确渲染
            # 无需对Rich标签进行预处理，直接使用Rich.Console渲染
            
            # 检测和处理代码块，为其应用高亮
            code_blocks = detect_code_blocks(text)
            
            # 如果找到代码块，直接使用Rich的语法高亮功能
            if code_blocks:
                # 先输出普通文本
                content_parts = []
                last_end = 0
                
                for block in sorted(code_blocks, key=lambda x: x["start"]):
                    # 添加代码块前的文本
                    if block["start"] > last_end:
                        pre_text = text[last_end:block["start"]]
                        if pre_text.strip():
                            content_parts.append(pre_text)
                    
                    # 获取代码块信息
                    lang = block["language"]
                    code = block["content"]
                    
                    # 使用面板渲染代码块，提供更美观的效果
                    if lang.lower() in ["python", "py"]:
                        title = "Python代码"
                        border_style = "cyan"
                    elif lang.lower() in ["bash", "sh", "shell", "命令"]:
                        title = "Bash脚本"
                        border_style = "green"
                    elif lang.lower() in ["javascript", "js"]:
                        title = "JavaScript代码"
                        border_style = "yellow"
                    elif lang.lower() in ["html"]:
                        title = "HTML"
                        border_style = "bright_blue"
                    elif lang.lower() in ["css"]:
                        title = "CSS"
                        border_style = "magenta"
                    elif lang.lower() in ["json"]:
                        title = "JSON"
                        border_style = "bright_green"
                    else:
                        title = f"{lang.capitalize()} 代码"
                        border_style = "blue"
                    
                    # 创建语法高亮对象
                    syntax_theme = "monokai" if HAS_TRUECOLOR else "vim"
                    
                    try:
                        # 使用Rich的Syntax对象实现更好的代码高亮
                        syntax = Syntax(
                            code.strip(),
                            lang,
                            theme=syntax_theme,
                            line_numbers=len(code.splitlines()) > 5,
                            word_wrap=True,
                            indent_guides=True,
                            background_color="default"
                        )
                        
                        # 创建带有标题的面板
                        panel = Panel(
                            syntax,
                            title=f"[bold {border_style}]{title}[/bold {border_style}]",
                            border_style=border_style,
                            box=box.ROUNDED
                        )
                        
                        console.print(panel)
                    except Exception as e:
                        # 如果特定语言无法高亮，回退到默认文本显示
                        console.print(f"[bold {border_style}]{title}[/bold {border_style}]")
                        console.print(code)
                    
                    last_end = block["end"]
                
                # 添加最后一个代码块后的文本
                if last_end < len(text):
                    post_text = text[last_end:]
                    if post_text.strip():
                        content_parts.append(post_text)
                
                # 渲染代码块之外的Markdown文本
                for part in content_parts:
                    if part.strip():
                        try:
                            # 使用Rich的Markdown渲染器处理普通文本
                            md = Markdown(part)
                            console.print(md)
                        except Exception as e:
                            # 如果Rich的Markdown渲染器出错，尝试直接输出文本
                            # 直接使用console.print，它会解析和渲染Rich标签
                            console.print(part)
            else:
                # 确保代码块闭合
                if text.count('```') % 2 != 0:
                    text += '\n```'
                
                # 如果没有代码块，直接渲染整个文本
                try:
                    # 使用Rich的Markdown渲染器
                    md = Markdown(text)
                    console.print(md)
                except Exception as e:
                    # 如果Rich的Markdown渲染器出错，使用console.print直接渲染
                    # 这样可以确保Rich标签被正确解析
                    print(f"Markdown渲染出错，使用Rich标签直接渲染: {e}")
                    console.print(text)
        except Exception as e:
            print(f"Markdown渲染出错: {e}")
            print(text)  # 出错时直接打印
    else:
        print(text)

def execute_command(command: str) -> Tuple[str, bool]:
    """执行Shell命令并返回结果
    
    Args:
        command: 要执行的Shell命令
        
    Returns:
        命令输出结果和执行是否成功的标志
    """
    try:
        # 直接在当前shell中执行命令，不改变目录
        print(colored_text(f"执行命令: {command}", Fore.BLUE))
        
        # 执行命令并实时显示输出
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时显示输出
        stdout_output = ""
        stderr_output = ""
        
        # 实时读取和显示标准输出
        for line in iter(process.stdout.readline, ""):
            if line:
                print(line, end="")
                stdout_output += line
        
        # 读取错误输出
        for line in iter(process.stderr.readline, ""):
            if line:
                print(colored_text(line, Fore.RED), end="")
                stderr_output += line
        
        # 等待进程完成
        return_code = process.wait()
        success = return_code == 0
        
        output = stdout_output
        if stderr_output and not success:
            output += "\n" + stderr_output
            
        if not success:
            print(colored_text(f"命令执行失败，返回码: {return_code}", Fore.RED))
        else:
            print(colored_text("命令执行成功", Fore.GREEN))
            
        return output, success
    except Exception as e:
        error_msg = str(e)
        print(colored_text(f"执行命令出错: {error_msg}", Fore.RED))
        return error_msg, False

def is_dangerous_command(command: str) -> bool:
    """检查命令是否危险
    
    Args:
        command: 要检查的命令
        
    Returns:
        如果命令危险则返回True
    """
    # 危险命令关键字列表
    dangerous_patterns = [
        r"\brm\s+(-[rf]+\s+)?(\/|~|\.\.)",  # 删除重要目录
        r"\bmv\s+\S+\s+(\/|~)",  # 移动到重要目录
        r"\bdd\s+",  # dd命令
        r"\bformat\b",  # 格式化
        r"\bmkfs\b",  # 创建文件系统
        r"\b(halt|poweroff|shutdown|reboot)\b",  # 关机命令
        r":(){.*};:",  # Fork炸弹
        r"\bchmod\s+-[R].*777\b",  # 递归chmod 777
        r"\b(wget|curl).*\|\s*(bash|sh)\b",  # 下载并执行脚本
    ]
    
    # 检查命令是否匹配危险模式
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            return True
            
    return False

def detect_code_blocks(text: str) -> List[Dict[str, str]]:
    """从文本中检测代码块
    
    Args:
        text: 要分析的文本
        
    Returns:
        检测到的代码块列表，每项包含类型和内容
    """
    # 如果导入了rich_renderer，优先使用其中的代码块检测
    if HAS_RICH_RENDERER:
        try:
            return rich_detect_code_blocks(text)
        except Exception:
            pass  # 如果出错则回退到默认实现
            
    # 匹配Markdown代码块 ```语言\n代码\n```
    code_blocks = []
    pattern = r"```(\w*)\n([\s\S]*?)\n```"
    
    for match in re.finditer(pattern, text):
        lang = match.group(1) or "text"
        code = match.group(2)
        
        # 处理特殊的"命令"类型，将其映射为bash
        if lang.lower() == "命令":
            lang = "bash"
            is_command = True
        else:
            is_command = False
            
        code_blocks.append({
            "language": lang,
            "content": code,
            "start": match.start(),
            "end": match.end(),
            "is_command": is_command
        })
        
    return code_blocks

def suggest_filename(code_block: Dict[str, str]) -> str:
    """根据代码块内容推荐文件名
    
    Args:
        code_block: 代码块信息
        
    Returns:
        推荐的文件名
    """
    lang = code_block["language"].lower()
    content = code_block["content"]
    
    # 语言到文件扩展名的映射
    extensions = {
        "python": ".py",
        "py": ".py",
        "javascript": ".js",
        "js": ".js",
        "typescript": ".ts",
        "ts": ".ts",
        "html": ".html",
        "css": ".css",
        "json": ".json",
        "bash": ".sh",
        "shell": ".sh",
        "sh": ".sh",
        "ruby": ".rb",
        "go": ".go",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp",
        "c++": ".cpp",
        "rust": ".rs",
        "rs": ".rs",
    }
    
    # 尝试从内容中检测文件名
    filename_patterns = [
        r"(?:\/\/|#)\s*filename\s*:\s*(\S+)",  # // filename: name.ext
        r"\/\*\s*filename\s*:\s*(\S+)\s*\*\/", # /* filename: name.ext */
        r"<!--\s*filename\s*:\s*(\S+)\s*-->",  # <!-- filename: name.ext -->
    ]
    
    for pattern in filename_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    
    # 根据语言类型生成默认文件名
    ext = extensions.get(lang, ".txt")
    
    # 为主要语言类型生成更具体的文件名
    if lang in ["python", "py"]:
        if "def main" in content or "if __name__ == \"__main__\"" in content:
            return "main.py"
        elif "class" in content:
            # 尝试提取类名
            class_match = re.search(r"class\s+(\w+)", content)
            if class_match:
                return f"{class_match.group(1).lower()}.py"
    elif lang in ["js", "javascript"]:
        if "function main" in content or "const main" in content:
            return "main.js"
    elif lang in ["html"]:
        return "index.html"
    elif lang in ["sh", "bash", "shell"]:
        return "script.sh"
        
    # 默认名称
    return f"file_{int(time.time())}{ext}"

def write_to_file(filename: str, content: str) -> bool:
    """将内容写入文件
    
    Args:
        filename: 文件名
        content: 文件内容
        
    Returns:
        写入是否成功
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(colored_text(f"写入文件失败: {e}", Fore.RED))
        return False

def call_openai_api(messages: List[Dict[str, str]]) -> str:
    """使用新版OpenAI API调用，包含记忆增强
    
    Args:
        messages: 消息历史记录
        
    Returns:
        完整的响应文本
    """
    if not API_KEYS["openai"]:
        return colored_text(f"错误: 未配置OpenAI API密钥", Fore.RED)
    
    # 增强消息上下文
    enhanced_messages = context_enhancer.enhance_messages(messages)
    
    # 使用requests库模拟新版API调用
    headers = {
        "Authorization": f"Bearer {API_KEYS['openai']}", 
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_MAP["openai"],
        "messages": enhanced_messages,
        "stream": True
    }
    
    try:
        # 使用会话对象以便复用连接
        session = requests.Session()
        response = session.post(
            f"{API_ENDPOINTS['openai']}/chat/completions",
            headers=headers, 
            json=data, 
            proxies=proxies,
            timeout=60,
            stream=True
        )
        response.raise_for_status()
        
        # 返回响应流
        return response
    except Exception as e:
        print(colored_text(f"OpenAI API调用出错详情: {repr(e)}", Fore.RED))
        return None

def call_xai_api(messages: List[Dict[str, str]]) -> str:
    """使用新版XAI API调用，包含记忆增强
    
    Args:
        messages: 消息历史记录
        
    Returns:
        完整的响应文本
    """
    if not API_KEYS["xai"]:
        return colored_text(f"错误: 未配置XAI API密钥", Fore.RED)
    
    # 增强消息上下文
    enhanced_messages = context_enhancer.enhance_messages(messages)
    
    # 使用requests库模拟新版API调用
    headers = {
        "Authorization": f"Bearer {API_KEYS['xai']}", 
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_MAP["xai"],
        "messages": enhanced_messages,
        "stream": True
    }
    
    try:
        # 使用会话对象以便复用连接
        session = requests.Session()
        response = session.post(
            f"{API_ENDPOINTS['xai']}/chat/completions",
            headers=headers,
            json=data,
            proxies=proxies,
            timeout=60,
            stream=True
        )
        response.raise_for_status()
        
        # 返回响应流
        return response
    except Exception as e:
        print(colored_text(f"XAI API调用出错: {str(e)}", Fore.RED))
        return None

def call_deepseek_api(messages: List[Dict[str, str]]) -> str:
    """使用DeepSeek API调用，包含记忆增强
    
    Args:
        messages: 消息历史记录
        
    Returns:
        完整的响应文本
    """
    if not API_KEYS["deepseek"]:
        return colored_text(f"错误: 未配置DeepSeek API密钥", Fore.RED)
    
    # 增强消息上下文
    enhanced_messages = context_enhancer.enhance_messages(messages)
    
    headers = {
        "Authorization": f"Bearer {API_KEYS['deepseek']}", 
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_MAP["deepseek"],
        "messages": enhanced_messages,
        "stream": True
    }
    
    try:
        # 使用会话对象以便复用连接
        session = requests.Session()
        response = session.post(
            f"{API_ENDPOINTS['deepseek']}/chat/completions",
            headers=headers, 
            json=data, 
            proxies=proxies,
            timeout=60,
            stream=True
        )
        response.raise_for_status()
        
        # 返回响应流
        return response
    except Exception as e:
        print(colored_text(f"DeepSeek API调用出错: {str(e)}", Fore.RED))
        return None

def stream_response(model: str, messages: List[Dict[str, str]]) -> str:
    """流式获取API响应
    
    Args:
        model: 模型类型 (openai/deepseek/xai)
        messages: 消息历史记录
        
    Returns:
        完整的响应文本
    """
    if model == "openai" and API_KEYS["openai"]:
        response_stream = call_openai_api(messages)
    elif model == "xai" and API_KEYS["xai"]:
        response_stream = call_xai_api(messages)
    elif model == "deepseek" and API_KEYS["deepseek"]:
        response_stream = call_deepseek_api(messages)
    else:
        return colored_text(f"错误: 模型{model}不可用或未配置API密钥", Fore.RED)
    
    if response_stream is None:
        return colored_text(f"错误: 无法连接到{model}服务", Fore.RED)
    
    # 输出模型名称前缀，但不输出实际内容
    print(f"\n{Fore.GREEN}({model}){Style.RESET_ALL}：", end="", flush=True)
    
    # 使用旋转动画的进度指示器
    progress_thread = None
    progress_stop = threading.Event()
    
    def show_progress():
        spinner = DEFAULT_SPINNER
        i = 0
        while not progress_stop.is_set():
            sys.stdout.write(f"\r{Fore.GREEN}({model}){Style.RESET_ALL}：{spinner[i]} ")
            sys.stdout.flush()
            i = (i + 1) % len(spinner)
            time.sleep(0.1)
    
    # 开始进度线程
    progress_thread = threading.Thread(target=show_progress)
    progress_thread.daemon = True
    progress_thread.start()
    
    full_message = ""
    
    # 收集完整内容，但不显示
    try:
        for line in response_stream.iter_lines():
            if not line:
                continue
                
            # 解析SSE格式的数据
            line = line.decode('utf-8')
            if line.startswith("data: "):
                if line == "data: [DONE]":
                    break
                    
                try:
                    chunk_data = json.loads(line[6:])
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        delta = chunk_data["choices"][0].get("delta", {})
                        if "content" in delta:
                            content = delta["content"]
                            full_message += content
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(colored_text(f"\n解析响应出错: {str(e)}", Fore.RED))
    
        # 停止进度线程
        if progress_thread:
            progress_stop.set()
            progress_thread.join()
        
        # 清除进度指示器
        print("\r" + " " * 50 + "\r", end="")
        
        # 检查内容是否含有Rich标签
        has_rich_tags = bool(re.search(r'\[.*?\].*?\[/.*?\]', full_message))
        rich_available = os.getenv("RICH_AVAILABLE", "false").lower() == "true"
        use_markdown = os.getenv("USE_MARKDOWN", "true").lower() == "true"
        
        print()  # 添加空行，确保内容从新行开始
        
        # 优先处理Rich标签
        if has_rich_tags and rich_available:
            # 处理既有Rich标签又有代码块的情况
            code_blocks = detect_code_blocks(full_message)
            if code_blocks:
                # 有代码块，分段处理
                last_end = 0
                
                for block in sorted(code_blocks, key=lambda x: x["start"]):
                    # 添加代码块前的普通文本
                    if block["start"] > last_end:
                        pre_text = full_message[last_end:block["start"]]
                        if pre_text.strip():
                            # 检查这部分是否含有Rich标签
                            if re.search(r'\[.*?\].*?\[/.*?\]', pre_text):
                                if HAS_RICH_RENDERER:
                                    render_rich_tags(pre_text)
                                else:
                                    console.print(pre_text)
                            else:
                                print_with_typewriter(pre_text)
                    
                    # 渲染代码块
                    if HAS_RICH_RENDERER:
                        render_code_block(block["content"], block["language"])
                    else:
                        render_markdown(full_message[block["start"]:block["end"]])
                    
                    last_end = block["end"]
                
                # 添加最后一个代码块后的文本
                if last_end < len(full_message):
                    post_text = full_message[last_end:]
                    if post_text.strip():
                        # 检查这部分是否含有Rich标签
                        if re.search(r'\[.*?\].*?\[/.*?\]', post_text):
                            if HAS_RICH_RENDERER:
                                render_rich_tags(post_text)
                            else:
                                console.print(post_text)
                        else:
                            print_with_typewriter(post_text)
            else:
                # 只有Rich标签，没有代码块
                if HAS_RICH_RENDERER:
                    render_rich_tags(full_message)
                elif console is not None:
                    console.print(full_message)
                else:
                    print(full_message)
        # 处理Markdown内容
        elif use_markdown and rich_available:
            # 检测和处理代码块
            code_blocks = detect_code_blocks(full_message)
            
            if code_blocks:
                # 有代码块，分段处理
                last_end = 0
                
                for block in sorted(code_blocks, key=lambda x: x["start"]):
                    # 添加代码块前的普通文本（使用打字机效果）
                    if block["start"] > last_end:
                        pre_text = full_message[last_end:block["start"]]
                        if pre_text.strip():
                            print_with_typewriter(pre_text)
                    
                    # 渲染代码块
                    if HAS_RICH_RENDERER:
                        render_code_block(block["content"], block["language"])
                    else:
                        render_markdown(full_message[block["start"]:block["end"]])
                    
                    last_end = block["end"]
                
                # 添加最后一个代码块后的文本
                if last_end < len(full_message):
                    post_text = full_message[last_end:]
                    if post_text.strip():
                        print_with_typewriter(post_text)
            else:
                # 没有代码块，整体渲染为Markdown
                render_markdown(full_message)
        else:
            # 普通文本，使用打字机效果
            print_with_typewriter(full_message)
            
        return full_message
            
    except KeyboardInterrupt:
        # 用户中断输出
        if progress_thread:
            progress_stop.set()
            progress_thread.join()
            print("\n")
        return colored_text("用户已中断输出", Fore.YELLOW)
    
    except Exception as e:
        # 其他错误
        if progress_thread:
            progress_stop.set()
            progress_thread.join()
        return colored_text(f"处理响应时出错: {str(e)}", Fore.RED)

def fallback_response() -> str:
    """当所有API都失败时使用的本地回复
    
    Returns:
        随机的本地回复
    """
    responses = [
        "看起来网络有点问题，无法连接到服务器。",
        "API服务暂时不可用，请稍后再试。",
        "无法连接到AI服务，请检查你的网络连接。",
        "服务器似乎没有响应，请稍后再试。",
        "API调用失败，请确认你的API密钥是否有效。",
    ]
    import random
    return colored_text(random.choice(responses), Fore.YELLOW)

def process_response(response: str) -> Tuple[str, List[Dict[str, str]], List[str]]:
    """处理AI的响应，提取命令和代码块
    
    Args:
        response: AI的响应文本
        
    Returns:
        处理后的响应文本、代码块列表和命令列表
    """
    # 提取代码块
    code_blocks = detect_code_blocks(response)
    
    # 提取可能的命令行命令 (以!或$开头的行)
    commands = []
    command_pattern = r"^(?:\!|\$)\s*(.+)$"
    
    for line in response.split('\n'):
        match = re.match(command_pattern, line.strip())
        if match:
            cmd = match.group(1).strip()
            if cmd and not is_dangerous_command(cmd):
                commands.append(cmd)
    
    # 从响应中移除命令提示符，使显示更干净
    cleaned_response = re.sub(r"^(?:\!|\$)\s*(.+)$", r"\1", response, flags=re.MULTILINE)
    
    return cleaned_response, code_blocks, commands

def handle_commands(commands: List[str]) -> None:
    """处理检测到的命令
    
    Args:
        commands: 要处理的命令列表
    """
    for cmd in commands:
        # 跳过危险命令
        if is_dangerous_command(cmd):
            print(colored_text(f"拒绝执行潜在危险命令: {cmd}", Fore.RED))
            continue
            
        print(colored_text(f"！是否执行:`{cmd}` ?(y/n)", Fore.GREEN))
        choice = input().strip().lower()
        
        if choice == 'y':
            # 执行命令并显示结果
            output, success = execute_command(cmd)
            # 在execute_command内部已经输出结果
        else:
            print(colored_text("已取消执行", Fore.YELLOW))

def handle_code_blocks(code_blocks: List[Dict[str, str]]) -> None:
    """处理检测到的代码块
    
    Args:
        code_blocks: 代码块列表
    """
    if not code_blocks:
        return
        
    for block in code_blocks:
        suggested_filename = suggest_filename(block)
        language = block["language"]
        content = block["content"]
        is_command = block.get("is_command", False)
        
        # 提供文件的绝对路径
        current_dir = os.getcwd()
        full_path = os.path.join(current_dir, suggested_filename)
        
        # 区分命令和脚本的提示信息
        if is_command:
            block_type = "命令"
        else:
            block_type = f"{language}代码"
            
        print(colored_text(f"！检测到{block_type}块，是否写入文件{suggested_filename}?(y/n/e/rnm) y:写入 n:丢弃 e:显示内容 rnm:重命名", Fore.GREEN))
        choice = input().strip().lower()
        
        if choice == 'e':
            print(colored_text(f"代码内容:", Fore.BLUE))
            print(content)
            print(colored_text(f"！是否写入文件{suggested_filename}?(y/n/r/rnm) y:写入 n:丢弃 r:返回让模型修改[r 需要修改的内容] rnm:重命名", Fore.GREEN))
            choice = input().strip().lower()
            
        if choice.startswith('r') and choice != 'rnm':
            # 提取需要修改的内容
            modification = choice[1:].strip()
            if modification:
                return_message = f"请修改代码：{modification}"
                print(colored_text(f"正在请求修改...", Fore.BLUE))
                chat_once(return_message)
            else:
                print(colored_text("未提供修改内容，已取消", Fore.YELLOW))
        elif choice == 'rnm':
            # 允许用户重命名文件
            print(colored_text(f"请输入新的文件名:", Fore.GREEN))
            new_filename = input().strip()
            if new_filename:
                if not os.path.isabs(new_filename):
                    # 如果不是绝对路径，添加当前目录
                    full_path = os.path.join(current_dir, new_filename)
                else:
                    full_path = new_filename
                suggested_filename = os.path.basename(full_path)
                
                print(colored_text(f"！是否将{block_type}块写入文件{suggested_filename}?(y/n)", Fore.GREEN))
                if input().strip().lower() == 'y':
                    if write_to_file(full_path, content):
                        print(colored_text(f"！写入成功！文件位置: {full_path}", Fore.GREEN))
                        
                        # 处理可执行文件
                        handle_executable_file(full_path, language)
                else:
                    print(colored_text("已取消写入", Fore.YELLOW))
            else:
                print(colored_text("未提供有效的文件名，已取消", Fore.YELLOW))
        elif choice == 'y':
            # 写入文件
            if write_to_file(full_path, content):
                print(colored_text(f"！写入成功！文件位置: {full_path}", Fore.GREEN))
                
                # 处理可执行文件
                handle_executable_file(full_path, language)
            else:
                print(colored_text(f"写入文件失败", Fore.RED))
        else:
            print(colored_text("已取消写入", Fore.YELLOW))

def handle_executable_file(file_path: str, language: str) -> None:
    """处理可执行文件(添加执行权限并询问是否执行)
    
    Args:
        file_path: 文件路径
        language: 语言类型
    """
    # 对特定类型的文件询问是否执行
    if language in ["sh", "bash", "shell"] or file_path.endswith(".sh"):
        cmd = f"chmod +x {file_path}"
        print(colored_text(f"！是否执行:`{cmd}`? (y/n)", Fore.GREEN))
        if input().strip().lower() == 'y':
            output, success = execute_command(cmd)
            if success:
                print(colored_text("权限设置成功", Fore.GREEN))
                
                cmd = f"{file_path}"
                print(colored_text(f"！是否执行:`{cmd}`? (y/n)", Fore.GREEN))
                if input().strip().lower() == 'y':
                    output, success = execute_command(cmd)
                    # 结果已在execute_command中输出
    
    # 对Python文件询问是否执行
    elif language in ["python", "py"] or file_path.endswith(".py"):
        cmd = f"python3 {file_path}"
        print(colored_text(f"！是否执行:`{cmd}`? (y/n)", Fore.GREEN))
        if input().strip().lower() == 'y':
            output, success = execute_command(cmd)
            # 结果已在execute_command中输出
    
    # 对JavaScript文件询问是否使用Node执行
    elif language in ["javascript", "js"] or file_path.endswith(".js"):
        cmd = f"node {file_path}"
        print(colored_text(f"！是否执行:`{cmd}`? (y/n)", Fore.GREEN))
        if input().strip().lower() == 'y':
            output, success = execute_command(cmd)
            # 结果已在execute_command中输出

def chat_once(prompt: str, history=None, messages=None, memory_manager=None, context_enhancer=None, system_prompt=None, temperature=None, chat_id=None, max_tokens=None) -> str:
    """执行一次聊天交互，集成记忆功能
    
    Args:
        prompt: 用户输入的提示
        history: 历史记录，如果未提供则使用全局history
        messages: 额外消息
        memory_manager: 记忆管理器实例
        context_enhancer: 上下文增强器实例
        system_prompt: 系统提示
        temperature: 温度参数
        chat_id: 聊天ID
        max_tokens: 最大生成token数
        
    Returns:
        AI的响应消息
    """
    global current_model
    
    # 使用全局变量如果未提供
    local_history = history or globals().get('history', [])
    local_memory_manager = memory_manager or globals().get('memory_manager')
    local_context_enhancer = context_enhancer or globals().get('context_enhancer')
    
    # 添加当前时间戳到用户消息
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt_with_timestamp = f"[当前时间: {current_time}] {prompt}"
    
    # 添加到历史和记忆
    local_history.append({"role": "user", "content": prompt_with_timestamp})
    save_to_history("user", prompt_with_timestamp)
    
    # 显示用户输入("User"可以改)
    print(f"{Fore.CYAN}User：{Style.RESET_ALL}{prompt_with_timestamp}")
    
    # 启动思考动画
    stop_thinking = threading.Event()
    thinking_thread = threading.Thread(target=spinner_animation, args=(stop_thinking,))
    thinking_thread.daemon = True  # 设置为守护线程，确保主程序退出时线程也会退出
    thinking_thread.start()
    
    try:
        # 尝试不同的模型，优先使用当前选择的模型
        models_to_try = [current_model, "deepseek", "xai", "openai"]
        models_to_try = list(dict.fromkeys(models_to_try))  # 删除重复
        
        for model in models_to_try:
            try:
                if not API_KEYS[model]:
                    continue
                    
                # 停止思考动画
                stop_thinking.set()
                thinking_thread.join(timeout=1.0)  # 等待思考动画线程结束，设置超时
                
                # 尝试使用流式响应
                message = stream_response(model, local_history)
                
                # 检查是否有错误消息
                if message.startswith("错误:") or "请求错误" in message:
                    print(colored_text(f"模型 {model} 失败，尝试下一个...", Fore.YELLOW))
                    
                    # 重新启动思考动画
                    stop_thinking = threading.Event()
                    thinking_thread = threading.Thread(target=spinner_animation, args=(stop_thinking,))
                    thinking_thread.daemon = True
                    thinking_thread.start()
                    continue
                    
                # 成功获取响应
                local_history.append({"role": "assistant", "content": message})
                save_to_history("assistant", message)
                current_model = model  # 更新当前使用的模型
                
                # 处理响应中的命令和代码块
                processed_response, code_blocks, commands = process_response(message)
                
                # 处理命令
                if commands:
                    handle_commands(commands)
                
                # 处理代码块
                if code_blocks:
                    handle_code_blocks(code_blocks)
                
                # 检查是否需要将重要内容提升到中期记忆
                if local_memory_manager and hasattr(local_memory_manager, '_calculate_importance'):
                    if local_memory_manager._calculate_importance({"role": "assistant", "content": message}) > local_memory_manager.importance_threshold:
                        # 将重要回复直接添加到中期记忆
                        local_memory_manager.add_memory({
                            "role": "assistant",
                            "content": local_memory_manager._extract_core_content({"content": message}),
                            "original": message,
                            "query": prompt_with_timestamp
                        }, "mid")
                
                # 如果使用的是本地历史变量，确保更新全局历史
                if history is None and 'history' in globals():
                    globals()['history'] = local_history
                
                return message
            except Exception as e:
                print(colored_text(f"模型 {model} 出错: {str(e)}", Fore.RED))
                
                # 如果出错，重新启动思考动画
                if not stop_thinking.is_set():
                    stop_thinking.set()
                    thinking_thread.join(timeout=1.0)
                
                stop_thinking = threading.Event()
                thinking_thread = threading.Thread(target=spinner_animation, args=(stop_thinking,))
                thinking_thread.daemon = True
                thinking_thread.start()
        
        # 所有模型都失败了
        fallback_msg = fallback_response()
        local_history.append({"role": "assistant", "content": fallback_msg})
        save_to_history("assistant", fallback_msg)
        print_with_typewriter(fallback_msg, False)
        
        # 如果使用的是本地历史变量，确保更新全局历史
        if history is None and 'history' in globals():
            globals()['history'] = local_history
            
        return fallback_msg
    finally:
        # 确保思考动画停止
        if not stop_thinking.is_set():
            stop_thinking.set()
            thinking_thread.join(timeout=1.0)

def handle_memory_command(command: str) -> str:
    """处理记忆相关命令
    
    Args:
        command: 记忆命令
        
    Returns:
        命令执行结果
    """
    global memory_manager
    
    parts = command.split()
    if len(parts) < 2:
        # 显示帮助信息
        help_text = (
            "记忆命令使用方法:\n"
            "!memory show [数量] - 显示最近记忆\n"
            "!memory search/find <关键词> - 搜索记忆\n"
            "!memory add <文本/文件路径> - 添加内容到记忆\n"
            "!memory summary [today|week|month] - 总结特定时间段的记忆\n"
            "!memory migrate - 从历史记录文件迁移记忆\n"
            "!memory mark <ID> [important|normal|low] - 标记记忆重要性\n"
            "!memory topic <关键词> - 按主题查找记忆"
        )
        print(colored_text(help_text, Fore.CYAN))
        return help_text
        
    action = parts[1]
    
    if action == "show":
        # 显示最近记忆
        limit = int(parts[2]) if len(parts) > 2 else 5
        memories = memory_manager.get_recent_memories(limit)
        print_memories(memories)
        return f"已显示{len(memories)}条最近记忆"
        
    elif action == "search" or action == "find":
        # 搜索记忆
        if len(parts) < 3:
            print(colored_text("请提供搜索关键词", Fore.YELLOW))
            return "搜索格式: !memory search/find <关键词>"
            
        query = " ".join(parts[2:])
        memories = memory_manager.search_memories(query)
        print_memories(memories)
        return f"找到{len(memories)}条相关记忆"
        
    elif action == "add":
        # 添加记忆或文件
        if len(parts) < 3:
            print(colored_text("请提供要添加的内容或文件路径", Fore.YELLOW))
            return "添加格式: !memory add <文本/文件路径>"
            
        content = " ".join(parts[2:])
        
        # 检查是否是文件路径 - 优先检查是否存在文件
        content_parts = content.split(',')
        file_path = content_parts[0].strip()
        if os.path.exists(os.path.expanduser(file_path)):
            # 是文件路径，可能包含分类信息：路径,分类
            category = content_parts[1] if len(content_parts) > 1 else "file"
            
            # 添加文件到记忆系统
            success = add_file_to_memory(os.path.expanduser(file_path), category)
            if success:
                return f"已添加文件 '{os.path.basename(file_path)}' 到记忆系统"
            else:
                return "添加文件失败，请检查文件路径和权限"
        else:
            # 是文本内容
            memory_manager.add_memory({
                "role": "user",
                "content": content
            }, "mid")
            return f"已添加内容到记忆系统: '{content[:50]}...'"
        
    elif action == "summary":
        # 总结记忆
        timeframe = parts[2] if len(parts) > 2 else "today"
        if timeframe not in ["today", "week", "month"]:
            timeframe = "today"
            
        summary = memory_manager.summarize_memories(timeframe)
        print(colored_text(summary, Fore.CYAN))
        return summary
        
    elif action == "migrate":
        # 从历史记录迁移记忆
        limit = int(parts[2]) if len(parts) > 2 else 100
        memory_manager.migrate_from_history(limit)
        return f"已从历史记录迁移记忆(最多{limit}条)"
        
    elif action == "mark" or action == "star":
        # 标记记忆重要性
        if len(parts) < 3:
            print(colored_text("请提供记忆ID和重要性标记", Fore.YELLOW))
            return "格式: !memory mark <ID> [important|normal|low]"
            
        memory_id = parts[2]
        importance = "important"
        if len(parts) > 3:
            importance = parts[3]
        
        success = memory_manager.mark_memory_importance(memory_id, importance)
        if success:
            return f"已将记忆 #{memory_id} 标记为 {importance}"
        else:
            return f"标记记忆失败，请检查ID是否正确"
            
    elif action == "topic":
        # 按主题查找记忆
        if len(parts) < 3:
            print(colored_text("请提供主题关键词", Fore.YELLOW))
            return "格式: !memory topic <关键词>"
            
        topic = " ".join(parts[2:])
        memories = memory_manager.get_memories_by_topic(topic)
        print_memories(memories)
        return f"找到{len(memories)}条与主题「{topic}」相关的记忆"
        
    else:
        print(colored_text(f"未知记忆命令: {action}", Fore.YELLOW))
        return f"未知记忆命令: {action}"

def add_file_to_memory(file_path: str, category: str = "file") -> bool:
    """将文件内容添加到记忆系统
    
    Args:
        file_path: 文件路径
        category: 分类标签
    
    Returns:
        成功添加返回True，否则返回False
    """
    global memory_manager
    
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在 {file_path}")
            return False
            
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='latin-1') as f:
                file_content = f.read()
                
        # 提取文件名和扩展名
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # 根据扩展名推断语言类型
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.sh': 'bash',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.ts': 'typescript',
            '.md': 'markdown',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.txt': 'text'
        }
        
        lang = lang_map.get(file_ext, 'text')
        
        # 如果文件太大，截断内容
        max_file_size = 10000  # 大约10KB
        if len(file_content) > max_file_size:
            file_content = file_content[:max_file_size] + f"\n... (文件过大，已截断。完整文件位于: {file_path})"
            
        # 创建记忆内容
        memory_content = {
            "role": "system",
            "content": f"这是用户提供的{lang}文件 '{file_name}'，内容如下:\n```{lang}\n{file_content}\n```",
            "file_path": file_path,
            "file_type": lang,
            "category": category
        }
        
        # 添加到记忆系统
        if hasattr(memory_manager, 'add_memory_with_vectors'):
            # 如果是增强版记忆管理器，使用向量存储
            memory_manager.add_memory_with_vectors(memory_content, "mid")
        else:
            # 标准记忆管理器
            memory_manager.add_memory(memory_content, "mid")
        
        print(f"成功添加文件 '{file_name}' 到中期记忆")
        return True
        
    except Exception as e:
        print(f"添加文件到记忆系统时出错: {str(e)}")
        return False

def print_memories(memories: List[Dict]):
    """格式化显示记忆列表
    
    Args:
        memories: 记忆列表
    """
    if not memories:
        print(colored_text("没有找到相关记忆", Fore.YELLOW))
        return
        
    print(colored_text("\n===== 记忆内容 =====", Fore.CYAN))
    
    for i, memory in enumerate(memories, 1):
        content = memory.get("content", {})
        if isinstance(content, dict):
            role = content.get("role", "")
            text = content.get("content", "")
            
            # 获取时间和记忆类型
            time_str = memory.get("time", "")
            memory_type = memory.get("memory_type", "unknown")
            importance = memory.get("importance", 0)
            
            # 根据角色和记忆类型选择不同颜色
            if role == "user":
                role_color = Fore.CYAN
                role_display = "用户"
            elif role == "assistant":
                role_color = Fore.GREEN
                role_display = "助手"
            else:
                role_color = Fore.WHITE
                role_display = role
                
            # 根据记忆类型选择不同背景
            if memory_type == "short":
                type_color = ""
            elif memory_type == "mid":
                type_color = Fore.YELLOW
            elif memory_type == "long":
                type_color = Fore.MAGENTA
            else:
                type_color = ""
                
            # 显示记忆头部信息
            header = f"[{i}] "
            if time_str:
                try:
                    mem_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
                    header += f"{mem_time.strftime('%Y-%m-%d %H:%M')} "
                except ValueError:
                    header += f"{time_str} "
                    
            header += f"{type_color}[{memory_type}]{Style.RESET_ALL} "
            header += f"{role_color}{role_display}{Style.RESET_ALL}"
            
            if importance > 0:
                stars = int(importance * 5)
                header += f" {'★' * stars}{'☆' * (5 - stars)}"
                
            print(colored_text(header, Fore.WHITE))
            
            # 截断过长的文本
            if len(text) > 200:
                print(f"{text[:200]}...")
            else:
                print(text)
        else:
            # 直接显示内容
            print(colored_text(f"[{i}] 记忆:", Fore.WHITE))
            content_str = str(content)
            if len(content_str) > 200:
                print(f"{content_str[:200]}...")
            else:
                print(content_str)
            
        print("-" * 40)

def fix_zsh_command(command: str) -> str:
    """修复在zsh中使用的命令，特别是处理感叹号问题
    
    Args:
        command: 原始命令
        
    Returns:
        处理后的命令
    """
    # 如果命令以感叹号开头，在zsh中会被解释为历史扩展
    # 我们需要在感叹号前加反斜杠来转义它
    if command.startswith('!'):
        return '\\' + command
    return command

def main():
    """主函数，处理命令行参数并启动程序"""
    global current_model, history, memory_manager, context_enhancer

    # 设置命令行参数
    parser = argparse.ArgumentParser(description='GPT Terminal Client')
    parser.add_argument('prompt', nargs='?', help='Initial prompt to send to the model')
    parser.add_argument('-f', '--file', help='Read prompt from file')
    parser.add_argument('-s', '--system', help='System prompt to use')
    parser.add_argument('-i', '--interactive', action='store_true', help='Start in interactive mode')
    parser.add_argument('-d', '--direct', help='Send a single prompt and exit')
    parser.add_argument('-t', '--temperature', type=float, help='Temperature parameter')
    parser.add_argument('-m', '--max-tokens', type=int, help='Maximum tokens to generate')
    parser.add_argument('-c', '--chat-history', type=str, help='Path to chat history file')
    parser.add_argument('--model', choices=['g', 'd', 'x'], help='Model to use (g=openai, d=deepseek, x=xai)')
    args = parser.parse_args()
    
    # 在启动时打印使用zsh的提示
    if 'zsh' in os.environ.get('SHELL', ''):
        print(colored("\n注意: 您正在使用zsh shell，使用记忆命令时，请用以下方式之一:", "yellow"))
        print(colored("  1. 在单引号中使用: '!memory show 10'", "yellow"))
        print(colored("  2. 转义感叹号: \\!memory show 10", "yellow"))
        print(colored("  3. 在交互模式下使用 (无需转义)", "yellow"))
        print()

    # 确保配置目录存在
    ensure_config_dir()

    # 初始化记忆管理器
    memory_manager = EnhancedMemoryManager(CONFIG_DIR)
    
    # 初始化上下文增强器
    context_enhancer = ImprovedContextEnhancer(memory_manager, DEFAULT_SYSTEM_PROMPT)

    # 初始化history
    history = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
    history_file = args.chat_history or HISTORY_FILE
    load_history(history_file)

    # 从文件读取提示
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                args.prompt = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return

    # 设置模型
    if args.model:
        if args.model == 'g':
            current_model = 'openai'
        elif args.model == 'd':
            current_model = 'deepseek'
        elif args.model == 'x':
            current_model = 'xai'

    # 设置系统提示
    system_prompt = args.system or DEFAULT_SYSTEM_PROMPT
    
    # 设置参数
    temperature = args.temperature
    max_tokens = args.max_tokens
    
    # 处理提示
    if args.direct:
        response = chat_once(args.direct)
    elif args.interactive or not args.prompt:
        interactive_mode()
    else:
        response = chat_once(args.prompt)
        save_history(history_file)

def interactive_mode():
    """交互模式，连续对话"""
    global current_model
    
    print(colored_text("\n欢迎使用TermGPT! 输入 'q' 或 'exit' 退出。", Fore.GREEN))
    print(colored_text(f"当前使用模型: {current_model}\n", Fore.BLUE))
    
    # 创建提示会话
    session = PromptSession()
    
    # 创建按键绑定
    kb = KeyBindings()
    
    # 添加Ctrl+C处理
    @kb.add('c-c')
    def _(event):
        event.app.exit(result="q")
    
    try:
        while True:
            # 获取用户输入 - 使用纯文本提示符，避免颜色代码问题
            user_input = session.prompt(
                ">>> ", 
                key_bindings=kb
            )
            
            # 检查退出命令
            if user_input.lower() in ['q', 'quit', 'exit']:
                print(colored_text("再见！", Fore.GREEN))
                break
            
            # 检查是否是记忆管理命令
            if user_input.startswith("tgptm "):
                # 去掉tgptm前缀，转换为记忆命令
                memory_cmd = user_input[6:]  # 跳过"tgptm "
                result = handle_memory_command(f"!memory {memory_cmd}")
                print(result)
                continue
                
            # 处理用户输入
            if user_input.strip():
                response = chat_once(user_input)
    except KeyboardInterrupt:
        print(colored_text("\n已退出，再见！", Fore.GREEN))
    except Exception as e:
        print(colored_text(f"发生错误: {str(e)}", Fore.RED))

if __name__ == "__main__":
    main()
