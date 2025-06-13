#!/bin/bash

# Ganaterm安装脚本
echo "开始安装Ganaterm..."

# 创建配置目录
CONFIG_DIR="$HOME/.config/ganaterm"
mkdir -p "$CONFIG_DIR"

# 复制必要文件
echo "正在复制配置文件到 $CONFIG_DIR..."
cp .env.example "$CONFIG_DIR/.env" 2>/dev/null || echo "注意：未找到.env.example文件，请手动创建.env文件"
cp aliases.sh "$CONFIG_DIR/"
cp ganaterm.py "$CONFIG_DIR/"

# 创建虚拟环境目录结构（如果需要实际的虚拟环境，取消注释下面的代码）
mkdir -p "$CONFIG_DIR/venv/bin"
touch "$CONFIG_DIR/venv/bin/activate"

# 如果需要创建真正的虚拟环境，取消注释以下行
# echo "正在创建Python虚拟环境..."
# cd "$CONFIG_DIR"
# python3 -m venv venv
# source venv/bin/activate
# pip install -r ../requirements.txt
# deactivate
# cd - > /dev/null

# 安装依赖
echo "正在安装Python依赖..."
pip install -r requirements.txt

# 添加别名到shell配置文件
shell_config=""
if [ -n "$ZSH_VERSION" ]; then
    shell_config="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    shell_config="$HOME/.bashrc"
else
    echo "未检测到支持的shell，请手动将别名添加到您的shell配置中"
    exit 1
fi

# 检查是否已经添加了source命令
if ! grep -q "source $CONFIG_DIR/aliases.sh" "$shell_config"; then
    echo "# Ganaterm配置" >> "$shell_config"
    echo "source $CONFIG_DIR/aliases.sh" >> "$shell_config"
    echo "已将别名添加到 $shell_config"
else
    echo "别名已存在于 $shell_config"
fi

echo "安装完成！请运行以下命令激活配置："
echo "source $shell_config"
echo ""
echo "然后，请编辑 $CONFIG_DIR/.env 文件，添加您的API密钥"
echo ""
echo "完成后，您可以使用以下命令："
echo "g [问题] - 使用OpenAI模型"
echo "d [问题] - 使用DeepSeek模型"
echo "x [问题] - 使用xAI模型" 