#!/bin/bash
# ganaterm终端助手别名设置
# 将此文件内容添加到您的 ~/.zshrc 或 ~/.bashrc 文件中

# 定义别名 - 在原生shell中执行命令
alias g='ganaterm_cmd g'  # OpenAI GPT
alias d='ganaterm_cmd d'  # DeepSeek
alias x='ganaterm_cmd x'  # xAI Grok

# 模型切换快捷命令
alias use_xai='sed -i "s/MODEL_TYPE=.*/MODEL_TYPE=xai/" ~/.config/ganaterm/.env'
alias use_deepseek='sed -i "s/MODEL_TYPE=.*/MODEL_TYPE=deepseek/" ~/.config/ganaterm/.env'
alias use_openai='sed -i "s/MODEL_TYPE=.*/MODEL_TYPE=openai/" ~/.config/ganaterm/.env'

# ganaterm主函数 - 直接在当前目录运行，不要切换目录
ganaterm_cmd() {
    # 保存当前目录
    CURRENT_DIR=$(pwd)
    
    # 启动虚拟环境但不切换目录
    source ~/.config/ganaterm/venv/bin/activate
    
    # 设置model参数
    model=$1
    shift
    if [[ -z "$model" ]]; then model="d"; fi  # 默认使用DeepSeek
    
    # 在当前目录运行python脚本
    python3 ~/.config/ganaterm/gpt_terminal.py "$model" "$@"
    
    # 退出虚拟环境
    deactivate
}

# 安装说明：
# 1. 复制这个文件到 ~/.config/ganaterm/ 目录
# 2. 在您的 ~/.zshrc 或 ~/.bashrc 中添加: source ~/.config/ganaterm/aliases.sh
# 3. 重新加载配置: source ~/.zshrc 或 source ~/.bashrc
# 4. 现在您可以使用 g/d/x 命令快速启动不同的AI助手
