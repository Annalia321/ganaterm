#!/bin/bash
# ganaterm终端助手别名设置
# 将此文件内容添加到您的 ~/.zshrc 或 ~/.bashrc 文件中

# TermGPT终端助手
termgpt() {
    cd ~/.config/ganaterm
    source venv/bin/activate 2>/dev/null || echo "警告：虚拟环境不存在，尝试直接执行"
    model=$1
    shift
    if [[ -z "$model" ]]; then model="d"; fi  # 默认使用deepseek
    python3 ganaterm.py "$model" "$@"
    deactivate 2>/dev/null
    cd - > /dev/null  # 返回原目录，不输出路径信息
}

# TermGPT快捷命令
alias g='termgpt g'
alias d='termgpt d'
alias x='termgpt x'

# 模型切换快捷命令
alias use_xai='sed -i "s/MODEL_TYPE=.*/MODEL_TYPE=xai/" ~/.config/ganaterm/.env'
alias use_deepseek='sed -i "s/MODEL_TYPE=.*/MODEL_TYPE=deepseek/" ~/.config/ganaterm/.env'
alias use_openai='sed -i "s/MODEL_TYPE=.*/MODEL_TYPE=openai/" ~/.config/ganaterm/.env'

# 安装说明：
# 1. 复制这个文件到 ~/.config/ganaterm/ 目录
# 2. 在您的 ~/.zshrc 或 ~/.bashrc 中添加: source ~/.config/ganaterm/aliases.sh
# 3. 重新加载配置: source ~/.zshrc 或 source ~/.bashrc
# 4. 现在您可以使用 g/d/x 命令快速启动不同的AI助手

# 可选提示信息，如果不需要可以注释掉
# echo "Ganaterm助手已加载，可使用以下命令："
# echo "g [问题] - 使用OpenAI模型"
# echo "d [问题] - 使用DeepSeek模型"
# echo "x [问题] - 使用xAI模型"
