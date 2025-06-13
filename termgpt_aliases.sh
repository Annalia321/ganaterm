#!/bin/bash

# TermGPT终端助手
termgpt() {
    cd ~/.config/termgpt
    source venv/bin/activate
    model=$1
    shift
    if [[ -z "$model" ]]; then model="d"; fi  # 默认使用deepseek
    python3 gpt_terminal.py "$model" "$@"
    deactivate
    cd - > /dev/null  # 返回原目录，不输出路径信息
}

# TermGPT快捷命令
alias g='termgpt g'
alias d='termgpt d'
alias x='termgpt x'

# 输出加载信息（可以注释掉此行以避免每次加载shell都显示）
# echo "TermGPT快捷命令已加载 (g/d/x)" 