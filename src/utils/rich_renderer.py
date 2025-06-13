#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rich渲染模块 - 提供更美观的终端UI渲染
"""

import re
import sys
from datetime import datetime
import os
from typing import List, Dict, Any, Optional, Tuple
import time

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.box import DOUBLE, ROUNDED, HEAVY
from rich import box
from rich.style import Style
from rich.theme import Theme

# 创建自定义主题
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
    "markdown.bold": "bold bright_blue",
    "markdown.warning_text": "bold red on yellow",
    # 添加P10K风格样式
    "p10k.segment": "bright_white on blue",
    "p10k.arrow": "bright_white",
    "p10k.prompt": "bright_green",
    "p10k.error": "bright_white on red",
    "p10k.success": "bright_white on green",
})

# 创建控制台对象 - 修改终端宽度获取
try:
    term_width = os.get_terminal_size().columns
except:
    term_width = 100

console = Console(width=term_width, color_system="truecolor", theme=CUSTOM_THEME)

def render_markdown_text(text: str) -> None:
    """使用Rich渲染Markdown文本
    
    Args:
        text: Markdown格式的文本
    """
    # 特殊处理：确保标题和粗体/代码块正确渲染
    # 在标题和粗体/代码块之间添加更多空行以确保正确识别
    text = re.sub(r'(#{1,6}[^\n]+)\n\s*(\*\*)', r'\1\n\n\2', text)
    text = re.sub(r'(#{1,6}[^\n]+)\n\s*(```)', r'\1\n\n\2', text)
    
    # 处理粗体标记，确保Rich正确识别
    text = re.sub(r'\*\*([^*\n]+?)\*\*', r'__\1__', text)
    
    # 处理代码块边距
    text = re.sub(r'```(\w*)\n', r'```\1\n\n', text)
    text = re.sub(r'\n```', r'\n\n```', text)
    
    md = Markdown(text)
    console.print(md)

def detect_code_blocks(text: str) -> List[Dict[str, Any]]:
    """从文本中检测代码块
    
    Args:
        text: 要分析的文本
        
    Returns:
        检测到的代码块列表，每项包含语言和内容
    """
    # 匹配Markdown代码块 ```语言\n代码\n```
    code_blocks = []
    pattern = r"```(\w*)\n([\s\S]*?)\n```"
    
    for match in re.finditer(pattern, text):
        lang = match.group(1) or "text"
        code = match.group(2)
        
        # 处理特殊的"命令"类型，将其映射为bash
        if lang.lower() == "命令":
            lang = "bash"
            
        code_blocks.append({
            "language": lang,
            "content": code,
            "start": match.start(),
            "end": match.end()
        })
    
    return code_blocks

# 添加新的辅助函数，增强Markdown处理能力
def preprocess_markdown(text: str) -> str:
    """预处理Markdown文本，修复常见问题
    
    Args:
        text: 原始Markdown文本
        
    Returns:
        处理后的Markdown文本
    """
    # 修复粗体和标题标记
    processed = text
    
    # 确保标题后有足够的空行
    processed = re.sub(r'(#{1,6}[^\n]+)\n([^\n])', r'\1\n\n\2', processed)
    
    # 确保粗体标记是连续的，不被误识别
    processed = re.sub(r'\*\*([^*\n]+?)\*\*', r'__\1__', processed) 
    
    # 确保代码块前后有空行
    processed = re.sub(r'([^\n])\n```', r'\1\n\n```', processed)
    processed = re.sub(r'```(\w*)\n', r'```\1\n\n', processed)
    processed = re.sub(r'\n```\n([^\n])', r'\n```\n\n\1', processed)
    
    return processed

# 扩展render_rich_tags函数，添加对内联粗体的额外支持
def render_rich_tags(text: str) -> None:
    """直接渲染包含Rich标签的文本
    
    Args:
        text: 包含Rich标签的文本
    """
    # 检查文本中是否有未转换的Markdown格式标记
    # 将**粗体**转换为[bold]粗体[/bold]
    text = re.sub(r'\*\*([^*]+?)\*\*', r'[bold]\1[/bold]', text)
    # 将*斜体*转换为[italic]斜体[/italic]
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'[italic]\1[/italic]', text)
    
    console.print(text)

def render_code_block(code: str, language: str, title: Optional[str] = None) -> None:
    """使用Rich渲染代码块
    
    Args:
        code: 代码内容
        language: 编程语言
        title: 可选的标题
    """
    # 选择合适的主题和边框
    theme = "monokai"
    border_style = "cyan"
    border_box = box.ROUNDED
    
    if language.lower() in ["bash", "shell", "sh", "命令"]:
        border_style = "green"
        title = title or "Bash脚本"
    elif language.lower() in ["python", "py"]:
        title = title or "Python代码"
    elif language.lower() in ["javascript", "js"]:
        border_style = "yellow"
        title = title or "JavaScript代码"
    elif language.lower() in ["html"]:
        border_style = "bright_blue"
        title = title or "HTML"
    elif language.lower() in ["css"]:
        border_style = "magenta"
        title = title or "CSS"
    elif language.lower() in ["json"]:
        border_style = "bright_green"
        title = title or "JSON"
    else:
        title = title or f"{language.capitalize()} 代码"
    
    # 创建语法高亮对象
    syntax = Syntax(
        code.strip(),
        language,
        theme=theme,
        line_numbers=True,
        word_wrap=True,
        indent_guides=True,
    )
    
    # 创建带有标题的面板
    panel = Panel(
        syntax,
        title=f"[bold {border_style}]{title}[/bold {border_style}]",
        border_style=border_style,
        box=border_box
    )
    
    console.print(panel)

def render_status_panel() -> None:
    """渲染系统状态面板"""
    # 构造状态文本
    status_text = """
CPU: [green]████████░░[/] 80%
内存: [yellow]█████████░[/] 90%
磁盘: [red]██████████[/] 100%
网络: [cyan]██████░░░░[/] 60%
"""
    
    # 创建状态面板
    panel = Panel(
        status_text,
        title="[bold]系统状态[/bold]",
        border_style="bright_blue",
        box=box.ROUNDED
    )
    
    console.print(panel)

def render_warning_panel(warning_text: str) -> None:
    """渲染警告面板
    
    Args:
        warning_text: 警告内容
    """
    formatted_text = f"""
[bold yellow]警告:[/bold yellow] {warning_text}
[bold]建议措施:[/bold] 请谨慎操作，确保安全。
"""
    
    panel = Panel(
        formatted_text,
        title="[bold red]⚠️ 警告信息[/bold red]",
        border_style="red",
        box=box.HEAVY
    )
    
    console.print(panel)

def render_typewriter_markdown(text: str, typing_speed: float = 0.01) -> None:
    """使用打字机效果渲染Markdown文本
    
    Args:
        text: Markdown格式的文本
        typing_speed: 打字速度延迟(秒)
    """
    # 预处理Markdown文本
    text = preprocess_markdown(text)
    
    # 检测代码块，将文本分段处理
    code_blocks = detect_code_blocks(text)
    
    if not code_blocks:
        # 如果没有代码块，使用简单的逐字符打字机效果
        processed_text = ""
        
        # 按行分割文本，逐行处理以避免光标闪烁问题
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                processed_text += '\n'
                print()  # 换行
                
            # 逐字符处理当前行
            line_text = ""
            for char in line:
                line_text += char
                # 清除当前行
                sys.stdout.write('\r' + ' ' * len(line_text) + '\r')
                # 输出新内容
                sys.stdout.write(line_text)
                sys.stdout.flush()
                time.sleep(typing_speed)
    else:
        # 有代码块，分段处理
        last_end = 0
        
        for block in sorted(code_blocks, key=lambda x: x["start"]):
            # 处理代码块前的文本（使用打字机效果）
            if block["start"] > last_end:
                pre_text = text[last_end:block["start"]]
                if pre_text.strip():
                    # 按行分割文本
                    lines = pre_text.split('\n')
                    for line in lines:
                        if not line.strip():
                            print()  # 空行直接输出
                            continue
                            
                        # 逐字符处理
                        line_text = ""
                        for char in line:
                            line_text += char
                            # 清除当前行
                            sys.stdout.write('\r' + ' ' * len(line_text) + '\r')
                            # 输出新内容
                            sys.stdout.write(line_text)
                            sys.stdout.flush()
                            time.sleep(typing_speed)
                        print()  # 行尾换行
            
            # 代码块一次性渲染（不使用打字机效果）
            render_code_block(block["content"], block["language"])
            
            last_end = block["end"]
        
        # 处理最后一个代码块后的文本
        if last_end < len(text):
            post_text = text[last_end:]
            if post_text.strip():
                # 按行处理
                lines = post_text.split('\n')
                for line in lines:
                    if not line.strip():
                        print()  # 空行直接输出
                        continue
                        
                    # 逐字符处理
                    line_text = ""
                    for char in line:
                        line_text += char
                        # 清除当前行
                        sys.stdout.write('\r' + ' ' * len(line_text) + '\r')
                        # 输出新内容
                        sys.stdout.write(line_text)
                        sys.stdout.flush()
                        time.sleep(typing_speed)
                    print()  # 行尾换行

def render_typewriter_rich_tags(text: str, typing_speed: float = 0.01) -> None:
    """使用打字机效果渲染包含Rich标签的文本
    
    Args:
        text: 包含Rich标签的文本
        typing_speed: 打字速度延迟(秒)
    """
    # 处理Markdown格式标记转换为Rich标签
    text = re.sub(r'\*\*([^*]+?)\*\*', r'[bold]\1[/bold]', text)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'[italic]\1[/italic]', text)
    
    # 分离代码块
    code_blocks = detect_code_blocks(text)
    
    if not code_blocks:
        # 按行逐字显示
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                print()  # 换行
                
            if not line.strip():
                continue  # 空行直接跳过
                
            # 逐字显示当前行
            visible_text = ""
            for char in line:
                visible_text += char
                sys.stdout.write('\r' + ' ' * len(visible_text) + '\r')
                sys.stdout.write(visible_text)
                sys.stdout.flush()
                time.sleep(typing_speed)
    else:
        # 有代码块，分段处理
        last_end = 0
        
        for block in sorted(code_blocks, key=lambda x: x["start"]):
            # 处理代码块前的文本
            if block["start"] > last_end:
                pre_text = text[last_end:block["start"]]
                if pre_text.strip():
                    # 按行处理
                    lines = pre_text.split('\n')
                    for line in lines:
                        if not line.strip():
                            print()  # 空行直接输出
                            continue
                            
                        # 逐字符处理
                        line_text = ""
                        for char in line:
                            line_text += char
                            sys.stdout.write('\r' + ' ' * len(line_text) + '\r')
                            sys.stdout.write(line_text)
                            sys.stdout.flush()
                            time.sleep(typing_speed)
                        print()  # 行尾换行
            
            # 代码块直接渲染
            render_code_block(block["content"], block["language"])
            
            last_end = block["end"]
        
        # 处理最后一个代码块后的文本
        if last_end < len(text):
            post_text = text[last_end:]
            if post_text.strip():
                # 按行处理
                lines = post_text.split('\n')
                for line in lines:
                    if not line.strip():
                        print()  # 空行直接输出
                        continue
                        
                    # 逐字符处理
                    line_text = ""
                    for char in line:
                        line_text += char
                        sys.stdout.write('\r' + ' ' * len(line_text) + '\r')
                        sys.stdout.write(line_text)
                        sys.stdout.flush()
                        time.sleep(typing_speed)
                    print()  # 行尾换行

# 如果检测到系统有pv命令，提供一个使用pv的打字机渲染函数
def has_pv_command():
    """检查系统是否安装了pv命令"""
    import shutil
    return shutil.which("pv") is not None

def render_with_pv(text: str, rate: int = 100):
    """使用pv命令实现打字机效果
    
    Args:
        text: 要渲染的文本
        rate: 每分钟字符数
    """
    if not has_pv_command():
        # 如果没有pv命令，回退到普通渲染
        console.print(text)
        return
        
    import subprocess
    import tempfile
    
    # 使用临时文件存储渲染结果
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp_path = tmp.name
        
        # 使用pv命令实现打字效果
        process = subprocess.Popen(
            ["pv", "-qL", str(rate)], 
            stdin=subprocess.PIPE, 
            stdout=tmp,
            text=True
        )
        process.communicate(input=text)
        
    # 读取临时文件内容
    with open(tmp_path, 'r') as f:
        content = f.read()
    
    # 删除临时文件
    import os
    os.unlink(tmp_path)
    
    # 渲染内容
    console.print(content)

# 如果直接运行此模块，执行简单的演示
if __name__ == "__main__":
    print("Rich渲染模块演示")
    
    # 测试Rich标签渲染
    print("\n== Rich标签渲染测试 ==")
    render_rich_tags("这是[bold cyan on grey11]彩色文本[/bold cyan on grey11]测试")
    
    # 测试Markdown渲染
    print("\n== Markdown渲染测试 ==")
    render_markdown_text("""
# 这是一级标题
## 这是二级标题

这是**粗体**文本，这是*斜体*文本。

- 列表项1
- 列表项2
  - 嵌套列表项

> 这是引用文本
""")
    
    # 测试代码块渲染
    print("\n== 代码块渲染测试 ==")
    render_code_block("""
def hello():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello()
""", "python", "示例Python代码")
    
    # 测试状态面板
    print("\n== 状态面板测试 ==")
    render_status_panel()
    
    # 测试警告面板
    print("\n== 警告面板测试 ==")
    render_warning_panel("这是一个警告消息，请注意！") 