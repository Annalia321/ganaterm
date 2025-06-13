#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CONFIG_DIR=~/.config/ganaterm

# 处理RAG监控命令
handle_rag_command() {
    local rag_script="$SCRIPT_DIR/rag_manager.sh"
    
    if [ ! -f "$rag_script" ]; then
        echo "❌ 错误: RAG管理脚本不存在: $rag_script"
        return 1
    fi
    
    # 传递所有参数给RAG管理脚本
    bash "$rag_script" "$@"
}

# 如果参数为空，提供帮助信息
if [ $# -eq 0 ]; then
  echo "使用方法: $0 [选项] [提示词]"
  echo "选项:"
  echo "  -i, --interactive  进入交互模式"
  echo "  -h, --help         显示帮助信息"
  echo "  g                  使用 OpenAI 模型 (别名)"
  echo "  d                  使用 DeepSeek 模型 (别名)"
  echo "  x                  使用 xAI 模型 (别名)"
  echo "  tgptm <命令>       内存管理命令"
  exit 0
fi

# 设置环境变量，避免重复初始化消息
export TERMGPT_INIT_DONE=1

# 从虚拟环境中查找 Python 解释器
if [ -f "$CONFIG_DIR/venv/bin/python" ]; then
  PYTHON_PATH="$CONFIG_DIR/venv/bin/python"
elif [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
  PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
else
  PYTHON_PATH=$(which python3)
fi

# 处理命令行参数
case "$1" in
  -i|--interactive)
    shift
    $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" -i
    ;;
  -h|--help)
    shift
    echo "🤖 GanaTerm - 终端AI助手"
    echo "======================="
    echo "可用模型别名:"
    echo "  tgpt     - 默认GPT模型"
    echo "  g        - GPT模型(简写)"
    echo "  d        - DeepSeek模型" 
    echo "  x        - xAI模型"
    echo "  tgpti    - 交互模式"
    echo ""
    echo "内存管理命令:"
    echo "  tgptm show [数量]      - 显示记忆列表"
    echo "  tgptm search [关键词]  - 搜索记忆内容" 
    echo "  tgptm add [文件路径]   - 添加文件到记忆"
    echo ""
    echo "RAG监控管理:"
    echo "  tgptr start           - 启动智能RAG监控"
    echo "  tgptr stop            - 停止RAG监控"
    echo "  tgptr status          - 查看监控状态"
    echo "  tgptr logs            - 查看监控日志"
    echo ""
    echo "注意: 在zsh中使用带!的命令时请用单引号包围"
    echo "示例: g '如何解决这个bug!'"
    ;;
  g)
    shift
    if [ $# -eq 0 ]; then
      # 如果没有其他参数，进入交互模式
      $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" -i --model g
    else
      # 处理可能包含感叹号的提示词
      prompt="$*"
      if [[ "$SHELL" == *"zsh"* && "$prompt" == *"!"* ]]; then
        # zsh中感叹号需要特殊处理
        $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" --model g "$prompt"
      else
        $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" --model g "$prompt"
      fi
    fi
    ;;
  d)
    shift
    if [ $# -eq 0 ]; then
      # 如果没有其他参数，进入交互模式
      $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" -i --model d
    else
      # 处理可能包含感叹号的提示词
      prompt="$*"
      if [[ "$SHELL" == *"zsh"* && "$prompt" == *"!"* ]]; then
        # zsh中感叹号需要特殊处理
        $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" --model d "$prompt"
      else
        $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" --model d "$prompt"
      fi
    fi
    ;;
  x)
    shift
    if [ $# -eq 0 ]; then
      # 如果没有其他参数，进入交互模式
      $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" -i --model x
    else
      # 处理可能包含感叹号的提示词
      prompt="$*"
      if [[ "$SHELL" == *"zsh"* && "$prompt" == *"!"* ]]; then
        # zsh中感叹号需要特殊处理
        $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" --model x "$prompt"
      else
        $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" --model x "$prompt"
      fi
    fi
    ;;
  tgptm)
    shift
    if [ $# -eq 0 ]; then
      echo "错误: 记忆命令缺少参数"
      echo "使用方法: tgptm <命令> [参数]"
      echo "示例:"
      echo "  tgptm show        - 显示最近记忆"
      echo "  tgptm find <关键词> - 搜索记忆"
      echo "  tgptm add <内容>   - 添加记忆"
      exit 1
    fi
    
    command="$1"
    shift
    
    case "$command" in
      show|find|search|add|summary|migrate|mark|topic)
        # 执行记忆命令
        if [[ "$SHELL" == *"zsh"* ]]; then
          # zsh需要特殊处理感叹号
          $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" "!memory $command $*"
        else
          $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" "!memory $command $*"
        fi
        ;;
      *)
        echo "未知记忆命令: $command"
        ;;
    esac
    ;;
  tgptr)
    shift  # 移除'tgptr'参数
    handle_rag_command "$@"
    exit $?
    ;;
  *)
    # 默认处理直接提问
    prompt="$*"
    if [[ "$SHELL" == *"zsh"* && "$prompt" == *"!"* ]]; then
      # zsh中感叹号需要特殊处理
      $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" "$prompt"
    else
      $PYTHON_PATH "$CONFIG_DIR/gpt_terminal.py" "$prompt"
    fi
    ;;
esac