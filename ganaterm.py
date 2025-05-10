#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ganaterm - 超轻量终端AI助手
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

import requests
from tqdm import tqdm
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from dotenv import load_dotenv
from colorama import Fore, Style, init

# 导入markdown渲染库
try:
    import rich
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.theme import Theme
    from rich.syntax import Syntax
    from rich.style import Style as RichStyle
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# 初始化colorama，支持彩色输出
init()

# ====== 常量定义 ======
CONFIG_DIR = os.path.expanduser("~/.config/ganaterm")
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
SYSTEM_PROMPT = (
    "你是一个轻量级终端AI助手，具有以下能力:\n"
    "1. 回答用户的技术问题，尤其擅长Linux/命令行/编程相关问题\n"
    "2. 提供命令行建议，并可以直接执行命令\n"
    "3. 生成代码并可以创建文件\n"
    "保持专业、简洁的回答风格，尽量少用emoji和表情符号。\n\n"
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
USE_MARKDOWN = HAS_RICH and os.getenv("USE_MARKDOWN", "true").lower() == "true"
if HAS_RICH:
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
history = [{"role": "system", "content": SYSTEM_PROMPT}]
current_model = "openai"  

# 获取代理设置
http_proxy = os.getenv("HTTP_PROXY")
https_proxy = os.getenv("HTTPS_PROXY")
proxies = {}
if http_proxy:
    proxies["http"] = http_proxy
if https_proxy:
    proxies["https"] = https_proxy

# ====== 辅助函数 ======
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

def load_history() -> List[Dict[str, str]]:
    """从文件加载聊天历史
    
    Returns:
        聊天历史记录列表
    """
    if not os.path.exists(HISTORY_FILE):
        return [{"role": "system", "content": SYSTEM_PROMPT}]
    
    result = [{"role": "system", "content": SYSTEM_PROMPT}]
    with open(HISTORY_FILE, 'r', encoding="utf-8") as f:
        for line in f:
            try:
                msg = json.loads(line.strip())
                result.append({"role": msg["role"], "content": msg["content"]})
            except json.JSONDecodeError:
                print(colored_text("历史文件解析错误，跳过这行", Fore.YELLOW))
    return result

def save_to_history(role: str, content: str):
    """保存消息到历史记录
    
    Args:
        role: 角色 (user/assistant)
        content: 消息内容
    """
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        line = json.dumps(
            {"time": str(datetime.now()), "role": role, "content": content},
            ensure_ascii=False
        )
        f.write(line + "\n")

def print_with_typewriter(text: str):
    """使用打字机效果打印文本
    
    Args:
        text: 要打印的文本
    """
    if not USE_TYPEWRITER:
        if USE_MARKDOWN:
            render_markdown(text)
        else:
            print(text)
        return
        
    # 为内联代码添加高亮，确保在打字效果前处理
    if USE_MARKDOWN:
        text_with_highlights = highlight_inline_code(text)
    else:
        text_with_highlights = text
        
    if HAS_PV:
        # 使用pv实现打字效果
        try:
            rate = int(len(text_with_highlights) / ((TYPING_SPEED_WPM / 60) / 5)) # 估算合适的速率
            
            if USE_MARKDOWN:
                # 临时文件方法，确保完整的渲染
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
                    tmp_path = tmp.name
                    process = subprocess.Popen(
                        ["pv", "-qL", str(rate)], 
                        stdin=subprocess.PIPE, 
                        stdout=tmp,
                        text=True
                    )
                    process.communicate(input=text_with_highlights)
                    
                # 读取临时文件并用Rich渲染
                with open(tmp_path, 'r') as f:
                    content = f.read()
                os.unlink(tmp_path)  # 删除临时文件
                render_markdown(content)
            else:
                process = subprocess.Popen(
                    ["pv", "-qL", str(rate)], 
                    stdin=subprocess.PIPE, 
                    stdout=sys.stdout,
                    text=True
                )
                process.communicate(input=text_with_highlights)
        except Exception as e:
            print(f"pv出错: {e}")
            if USE_MARKDOWN:
                render_markdown(text_with_highlights)
            else:
                print(text_with_highlights)  # 出错时直接打印
    else:
        # 手动实现打字效果
        if USE_MARKDOWN:
            # 如果使用Markdown，先收集完整文本再渲染
            full_text = ""
            delay = 60 / (TYPING_SPEED_WPM * 5)  # 估算每个字符的延迟时间
            for char in text_with_highlights:
                full_text += char
                # 使用简单的预览
                print(char, end='', flush=True)
                time.sleep(delay)
            print()  # 换行
            # 清除之前的输出并重新渲染
            sys.stdout.write("\033[F")  # 回到上一行
            sys.stdout.write("\033[K")  # 清除行
            render_markdown(full_text)
        else:
            delay = 60 / (TYPING_SPEED_WPM * 5)  # 估算每个字符的延迟时间
            for char in text_with_highlights:
                print(char, end='', flush=True)
                time.sleep(delay)
            print()  # 最后换行

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
    
    return processed_text

def render_markdown(text: str):
    """渲染Markdown文本
    
    Args:
        text: Markdown格式的文本
    """
    if HAS_RICH and USE_MARKDOWN:
        try:
            # 预处理代码块，确保代码块正确显示
            # 将模型可能输出的```命令，改为```bash以确保正确高亮
            text = re.sub(r'```命令\n', '```bash\n', text)
            
            # 预处理内联代码，为inline code添加背景颜色和高亮
            text_with_inline_highlights = highlight_inline_code(text)
            
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
                        pre_text = text_with_inline_highlights[last_end:block["start"]]
                        if pre_text.strip():
                            content_parts.append(pre_text)
                    
                    # 获取代码块信息
                    lang = block["language"]
                    code = block["content"]
                    
                    # 获取终端宽度，创建美观的边框
                    term_width = shutil.get_terminal_size().columns
                    
                    # 创建顶部边框和标题 - 使用兼容字符
                    lang_label = f" {lang} "
                    # 计算填充长度
                    fill_length = term_width - len(lang_label) - 4
                    if fill_length < 0:
                        fill_length = 0
                    
                    top_border = f"{CODE_BOX_TOP_LEFT}{CODE_BOX_HORIZONTAL*2}{lang_label}{CODE_BOX_HORIZONTAL * fill_length}{CODE_BOX_TOP_RIGHT}"
                    bottom_border = f"{CODE_BOX_BOTTOM_LEFT}{CODE_BOX_HORIZONTAL * (term_width - 2)}{CODE_BOX_BOTTOM_RIGHT}"
                    
                    console.print(top_border, style=CODE_BOX_STYLE)
                    
                    # 根据终端环境选择合适的语法高亮主题
                    syntax_theme = "monokai"
                    if IS_ZSH and not HAS_TRUECOLOR:
                        syntax_theme = "vim"  # vim主题在非真彩色终端上效果更好
                    
                    # 在zsh中可能需要简化显示
                    if IS_ZSH and not IS_TERM_SUPPORTED:
                        # 简化模式，只使用基本格式
                        for line in code.split('\n'):
                            console.print(f"{CODE_BOX_VERTICAL} {line.rstrip()}")
                    else:
                        # 尝试找到最合适的语言类型处理
                        try:
                            # 使用Rich的Syntax对象实现更好的代码高亮
                            syntax = Syntax(
                                code, 
                                lang, 
                                theme=syntax_theme,
                                line_numbers=len(code.splitlines()) > 5 and not IS_ZSH,  # 5行以上显示行号，但在zsh中禁用
                                word_wrap=True,
                                indent_guides=True and not IS_ZSH,  # zsh中禁用缩进指南
                                background_color="default"
                            )
                            console.print(syntax)
                        except Exception as e:
                            # 如果特定语言无法高亮，回退到默认文本显示
                            for line in code.split('\n'):
                                console.print(f"{CODE_BOX_VERTICAL} {line.rstrip()}")
                    
                    # 底部边框
                    console.print(bottom_border, style=CODE_BOX_STYLE)
                    
                    last_end = block["end"]
                
                # 添加最后一个代码块后的文本
                if last_end < len(text):
                    post_text = text_with_inline_highlights[last_end:]
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
                            console.print(part)
            else:
                # 确保代码块闭合
                if text.count('```') % 2 != 0:
                    text_with_inline_highlights += '\n```'
                
                # 如果没有代码块，直接渲染整个文本
                try:
                    console.print(Markdown(text_with_inline_highlights))
                except Exception as e:
                    # 如果Rich的Markdown渲染器出错，尝试分行输出
                    print(f"Markdown渲染出错，使用纯文本显示: {e}")
                    for line in text_with_inline_highlights.split('\n'):
                        console.print(line)
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
    """使用新版OpenAI API调用
    
    Args:
        messages: 消息历史记录
        
    Returns:
        完整的响应文本
    """
    if not API_KEYS["openai"]:
        return colored_text(f"错误: 未配置OpenAI API密钥", Fore.RED)
        
    # 使用requests库模拟新版API调用
    headers = {
        "Authorization": f"Bearer {API_KEYS['openai']}", 
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_MAP["openai"],
        "messages": messages,
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
        print(colored_text(f"OpenAI API调用出错: {str(e)}", Fore.RED))
        return None

def call_xai_api(messages: List[Dict[str, str]]) -> str:
    """使用新版XAI API调用
    
    Args:
        messages: 消息历史记录
        
    Returns:
        完整的响应文本
    """
    if not API_KEYS["xai"]:
        return colored_text(f"错误: 未配置XAI API密钥", Fore.RED)
        
    # 使用requests库模拟新版API调用
    headers = {
        "Authorization": f"Bearer {API_KEYS['xai']}", 
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_MAP["xai"],
        "messages": messages,
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
    """使用DeepSeek API调用
    
    Args:
        messages: 消息历史记录
        
    Returns:
        完整的响应文本
    """
    if not API_KEYS["deepseek"]:
        return colored_text(f"错误: 未配置DeepSeek API密钥", Fore.RED)
        
    headers = {
        "Authorization": f"Bearer {API_KEYS['deepseek']}", 
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL_MAP["deepseek"],
        "messages": messages,
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
        
    full_message = ""
    # 确保在新行开始输出模型回复
    print(f"\n{Fore.GREEN}({model}){Style.RESET_ALL}：", end="", flush=True)
    
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
                            print(content, end="", flush=True)
                            full_message += content
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(colored_text(f"\n解析响应出错: {str(e)}", Fore.RED))
        
        print()  # 确保最后换行
        return full_message
    except Exception as e:
        return colored_text(f"{model}请求错误: {str(e)}", Fore.RED)

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

def chat_once(prompt: str) -> str:
    """执行一次聊天交互
    
    Args:
        prompt: 用户输入的提示
        
    Returns:
        AI的响应消息
    """
    global current_model, history
    history.append({"role": "user", "content": prompt})
    save_to_history("user", prompt)
    
    # 显示用户输入("User"可以改)
    print(f"{Fore.CYAN}User：{Style.RESET_ALL}{prompt}")
    
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
                message = stream_response(model, history)
                
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
                history.append({"role": "assistant", "content": message})
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
        history.append({"role": "assistant", "content": fallback_msg})
        save_to_history("assistant", fallback_msg)
        print_with_typewriter(fallback_msg)
        return fallback_msg
    finally:
        # 确保思考动画停止
        if not stop_thinking.is_set():
            stop_thinking.set()
            thinking_thread.join(timeout=1.0)

def main():
    """主函数，处理命令行参数并启动程序"""
    global current_model, history
    
    # 确保配置目录存在
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print(colored_text("用法: ganaterm <模型> [问题]", Fore.YELLOW))
        print(colored_text("模型: g (GPT), d (DeepSeek), x (XAI)", Fore.YELLOW))
        print(colored_text("例如: ganaterm g '如何在Linux中查找文件?'", Fore.YELLOW))
        return

    # 测试兼容性并显示配置信息
    if len(sys.argv) > 1 and sys.argv[1] in ["--test", "-t"]:
        print(colored_text("Ganaterm 终端兼容性测试:", Fore.CYAN))
        print(f"Shell: {SHELL} (ZSH: {IS_ZSH})")
        print(f"终端: {TERM} (支持良好: {IS_TERM_SUPPORTED})")
        print(f"颜色支持: {COLORTERM} (真彩色: {HAS_TRUECOLOR})")
        print(f"Rich库可用: {HAS_RICH}")
        print(f"Markdown渲染: {USE_MARKDOWN}")
        
        if HAS_RICH:
            print("\n终端展示示例:")
            # 输出Rich库格式化测试
            console.print("[bold cyan]标题文本[/bold cyan]")
            console.print("[yellow]警告文本[/yellow]")
            console.print("[green]成功文本[/green]")
            console.print("内联代码示例: " + f"[{INLINE_CODE_STYLE}]`print('Hello')`[/{INLINE_CODE_STYLE}]")
            
            # 显示不同语言的代码高亮
            print("\n代码高亮测试:")
            python_code = "def hello():\n    print('Hello, world!')"
            term_width = shutil.get_terminal_size().columns
            
            # 创建边框
            lang_label = " python "
            fill_length = term_width - len(lang_label) - 4
            if fill_length < 0: 
                fill_length = 0
                
            top_border = f"{CODE_BOX_TOP_LEFT}{CODE_BOX_HORIZONTAL*2}{lang_label}{CODE_BOX_HORIZONTAL * fill_length}{CODE_BOX_TOP_RIGHT}"
            bottom_border = f"{CODE_BOX_BOTTOM_LEFT}{CODE_BOX_HORIZONTAL * (term_width - 2)}{CODE_BOX_BOTTOM_RIGHT}"
            
            # 显示Python代码测试
            console.print(top_border, style=CODE_BOX_STYLE)
            syntax = Syntax(
                python_code, 
                "python", 
                theme="monokai" if HAS_TRUECOLOR else "vim",
                line_numbers=False,
                word_wrap=True,
                background_color="default"
            )
            console.print(syntax)
            console.print(bottom_border, style=CODE_BOX_STYLE)
            
            print("\n配置提示:")
            if IS_ZSH:
                print(colored_text("- 您正在使用ZSH shell，为获得最佳显示效果:", Fore.YELLOW))
                print("  1. 请确保您的终端支持256色: export TERM=xterm-256color")
                print("  2. 如果您使用Oh-My-Zsh，请检查主题是否兼容")
            
            print(colored_text("\n如果代码块显示不正确，可以在~/.config/ganaterm/.env中设置:", Fore.CYAN))
            print("USE_MARKDOWN=false # 禁用富文本渲染")
            print("USE_TYPEWRITER=false # 禁用打字机效果")
        
        return

    # 设置模型
    model_flag = sys.argv[1]
    if model_flag == "g":
        current_model = "openai"
    elif model_flag == "d":
        current_model = "deepseek"
    elif model_flag == "x":
        current_model = "xai"
    else:
        print(colored_text("错误: 模型只能是 g (GPT), d (DeepSeek), x (XAI)", Fore.RED))
        return

    # 加载历史记录
    history = load_history()
    
    # 获取用户输入
    if len(sys.argv) > 2:
        # 从命令行参数获取
        prompt = " ".join(sys.argv[2:])
    else:
        # 交互式输入
        bindings = KeyBindings()
        @bindings.add('enter')
        def _(event):
            event.app.exit(result=event.app.current_buffer.text)
        @bindings.add('s-enter')
        def _(event):
            event.app.current_buffer.insert_text('\n')

        session = PromptSession(
            "你说（Shift+Enter 换行，Enter 提交）：", 
            multiline=True, 
            key_bindings=bindings
        )
        prompt = session.prompt()

    # 检查输入是否为空
    if not prompt.strip():
        print(colored_text("错误: 请输入问题", Fore.RED))
        return

    # 执行聊天
    chat_once(prompt)

if __name__ == "__main__":
    main()
