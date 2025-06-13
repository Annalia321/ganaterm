#!/bin/bash

# GanaTerm 安装脚本
# 自动安装和配置 GanaTerm 终端AI助手

set -e

echo "🚀 开始安装 GanaTerm..."

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CONFIG_DIR="$HOME/.config/ganaterm"

# 创建配置目录
echo "📁 创建配置目录..."
mkdir -p "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/memory"

# 复制必要文件到配置目录
echo "📋 复制配置文件..."
cp "$SCRIPT_DIR/gpt_terminal.py" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/smart_rag_monitor.py" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/wrapper.sh" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/rag_manager.sh" "$CONFIG_DIR/"

# 复制src目录
if [ -d "$SCRIPT_DIR/src" ]; then
    cp -r "$SCRIPT_DIR/src" "$CONFIG_DIR/"
fi

# 复制配置示例文件
if [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$CONFIG_DIR/"
fi

if [ -f "$SCRIPT_DIR/rag_config.example.json" ]; then
    cp "$SCRIPT_DIR/rag_config.example.json" "$CONFIG_DIR/"
fi

# 设置执行权限
chmod +x "$CONFIG_DIR/wrapper.sh"
chmod +x "$CONFIG_DIR/rag_manager.sh"
chmod +x "$CONFIG_DIR/smart_rag_monitor.py"

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
if [ ! -d "$CONFIG_DIR/venv" ]; then
    python3 -m venv "$CONFIG_DIR/venv"
fi

# 激活虚拟环境并安装依赖
echo "📦 安装Python依赖..."
source "$CONFIG_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

# 设置别名
echo "⚙️  配置命令别名..."
ALIAS_FILE="$HOME/.bashrc"
if [ "$SHELL" = "/usr/bin/zsh" ] || [ "$SHELL" = "/bin/zsh" ]; then
    ALIAS_FILE="$HOME/.zshrc"
fi

# 检查是否已经添加了别名
if ! grep -q "# GanaTerm aliases" "$ALIAS_FILE" 2>/dev/null; then
    echo "" >> "$ALIAS_FILE"
    echo "# GanaTerm aliases" >> "$ALIAS_FILE"
    echo "alias tgpt='$CONFIG_DIR/wrapper.sh'" >> "$ALIAS_FILE"
    echo "alias g='$CONFIG_DIR/wrapper.sh g'" >> "$ALIAS_FILE"
    echo "alias d='$CONFIG_DIR/wrapper.sh d'" >> "$ALIAS_FILE"
    echo "alias x='$CONFIG_DIR/wrapper.sh x'" >> "$ALIAS_FILE"
    echo "alias tgpti='$CONFIG_DIR/wrapper.sh -i'" >> "$ALIAS_FILE"
    echo "alias tgptm='$CONFIG_DIR/wrapper.sh tgptm'" >> "$ALIAS_FILE"
    echo "alias tgptr='$CONFIG_DIR/wrapper.sh tgptr'" >> "$ALIAS_FILE"
    echo "别名已添加到 $ALIAS_FILE"
else
    echo "别名已存在，跳过添加"
fi

echo ""
echo "✅ GanaTerm 安装完成！"
echo ""
echo "📝 下一步操作："
echo "1. 复制 .env.example 为 .env 并配置你的API密钥"
echo "   cp $CONFIG_DIR/.env.example $CONFIG_DIR/.env"
echo ""
echo "2. 编辑配置文件："
echo "   nano $CONFIG_DIR/.env"
echo ""
echo "3. 重新加载shell配置："
echo "   source $ALIAS_FILE"
echo ""
echo "4. 开始使用："
echo "   tgpt 你好"
echo "   g 写一个Python函数"
echo "   d 解释这段代码"
echo ""
echo "🎉 享受你的AI终端助手吧！" 