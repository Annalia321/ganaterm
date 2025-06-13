# Ganaterm - 智能终端AI助手

Ganaterm是一个功能强大的终端AI助手，支持多种大语言模型，提供智能对话、代码生成、命令执行等功能。

## 特性

- 多模型支持：OpenAI、DeepSeek、XAI等
- 智能记忆：短期、中期、长期记忆管理
- 上下文理解：智能分析和增强对话上下文
- 代码生成：支持多种编程语言
- 命令执行：安全的命令执行环境
- 美观界面：支持Markdown渲染和语法高亮

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/ganaterm.git
cd ganaterm
```

2. 运行安装脚本：
```bash
chmod +x run.sh
./run.sh
```

## 配置

1. 创建配置文件：
```bash
mkdir -p ~/.config/ganaterm
touch ~/.config/ganaterm/.env
```

2. 设置API密钥：
```bash
# OpenAI API密钥
OPENAI_API_KEY=your_openai_api_key

# DeepSeek API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key

# XAI API密钥
XAI_API_KEY=your_xai_api_key
```

## 使用方法

1. 启动程序：
```bash
./run.sh
```

2. 基本命令：
- `help` - 显示帮助信息
- `model list` - 显示可用模型
- `model switch <model>` - 切换模型
- `memory list` - 显示记忆列表
- `memory search <query>` - 搜索记忆
- `config show` - 显示配置
- `exit` - 退出程序

3. 聊天模式：
- 直接输入问题开始对话
- 支持多行输入（Shift+Enter换行）
- 支持代码块和命令执行

## 开发

1. 项目结构：
```
ganaterm/
├── src/
│   ├── core/           # 核心功能
│   ├── memory/         # 记忆管理
│   ├── utils/          # 工具函数
│   └── context/        # 上下文处理
├── ganaterm.py         # 主程序
├── run.sh             # 启动脚本
└── requirements.txt    # 依赖列表
```

2. 添加新功能：
- 在相应目录创建新模块
- 在`ganaterm.py`中导入和初始化
- 更新`requirements.txt`添加依赖

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License