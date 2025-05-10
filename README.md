# Ganaterm - 轻量级终端AI助手

[English](README.en.md) | 简体中文

Ganaterm是一个面向终端的轻量级AI助手程序，能够在无聊时与llm聊天、执行命令、生成并写入文件。

## 主要特性

- **模型api支持**：目前支持OpenAI、DeepSeek、xAI大语言模型
- **命令执行**：能够检测LLM响应中包含的命令并(y/n)执行（有安全检查）
- **轻量启动**：快速一键启动
- **打字效果**：支持打字机效果显示模型回复，提升交互体验(可选)
- **带有历史记忆**：支持历史对话记忆～

## 安装指南

## 安装

1. 克隆仓库
```bash
git clone https://github.com/Annalia321/ganaterm.git
cd ganaterm
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境
```bash
mkdir -p ~/.config/ganaterm
cp .env.example ~/.config/ganaterm/.env
# 编辑.env文件，添加你的API密钥
```

4. 设置别名
```bash
cp aliases.sh ~/.config/ganaterm/
echo "source ~/.config/ganaterm/aliases.sh" >> ~/.bashrc  # 或 ~/.zshrc
```

## 使用方法

### 快速命令

- `g [问题]` - 使用OpenAI模型
- `d [问题]` - 使用DeepSeek模型 
- `x [问题]` - 使用xAI(Grok)模型

例如：
```bash
g 如何在Linux中查找大文件?
```

### 命令执行

当AI建议命令时，会提示是否执行：

```
！是否执行:`find . -type f -size +100M` ?(y/n)
```

### 代码生成

当AI生成代码块时，会提示是否保存到文件：

```
！检测到python代码块，是否写入文件main.py?(y/n/e/rnm) y:写入 n:丢弃 e:显示内容 rnm:
！检测到python代码块，是否写入文件main.py?(y/n/e) y:写入 n:丢弃 e:显示内容
```

## 环境变量配置

`.env`文件支持以下配置：

- `OPENAI_API_KEY` - OpenAI API密钥
- `DEEPSEEK_API_KEY` - DeepSeek API密钥
- `XAI_API_KEY` - xAI API密钥
- `HTTP_PROXY/HTTPS_PROXY` - 代理设置
- `USE_TYPEWRITER` - 是否启用打字效果
- `TYPING_SPEED_WPM` - 打字速度设置


## 许可证


## 贡献

欢迎提交Pull Request或Issue来改进Ganaterm！
