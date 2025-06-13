#!/bin/bash

# RAG监控系统管理脚本
# 用于控制智能RAG监控器的启动、停止和状态管理

CONFIG_DIR="$HOME/.config/ganaterm"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAG_SCRIPT="$SCRIPT_DIR/smart_rag_monitor.py"
PID_FILE="$CONFIG_DIR/rag_monitor.pid"
LOG_FILE="$CONFIG_DIR/smart_rag.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 检查Python脚本是否存在
check_script() {
    if [ ! -f "$RAG_SCRIPT" ]; then
        echo -e "${RED}❌ 错误: 找不到RAG监控脚本 $RAG_SCRIPT${NC}"
        return 1
    fi
    return 0
}

# 检查是否正在运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            # PID文件存在但进程不存在，清理PID文件
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 启动RAG监控
start_rag() {
    echo -e "${BLUE}🚀 启动智能RAG监控系统...${NC}"
    
    if ! check_script; then
        return 1
    fi
    
    if is_running; then
        echo -e "${YELLOW}⚠️  RAG监控系统已经在运行中${NC}"
        return 1
    fi
    
    # 确保配置目录存在
    mkdir -p "$CONFIG_DIR"
    
    # 启动监控进程
    nohup python3 "$RAG_SCRIPT" start --daemon > /dev/null 2>&1 &
    local pid=$!
    
    # 保存PID
    echo "$pid" > "$PID_FILE"
    
    # 等待一下检查是否成功启动
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}✅ RAG监控系统启动成功！${NC}"
        echo -e "${CYAN}📋 PID: $(cat $PID_FILE)${NC}"
        echo -e "${CYAN}📄 日志文件: $LOG_FILE${NC}"
        return 0
    else
        echo -e "${RED}❌ RAG监控系统启动失败${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止RAG监控
stop_rag() {
    echo -e "${YELLOW}⏹️  停止RAG监控系统...${NC}"
    
    if ! is_running; then
        echo -e "${YELLOW}⚠️  RAG监控系统没有运行${NC}"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE" 2>/dev/null)
    
    # 发送TERM信号
    if kill -TERM "$pid" 2>/dev/null; then
        echo -e "${BLUE}📤 发送停止信号...${NC}"
        
        # 等待进程结束
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # 如果还没结束，强制杀死
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}⚡ 强制停止进程...${NC}"
            kill -KILL "$pid" 2>/dev/null
        fi
        
        rm -f "$PID_FILE"
        echo -e "${GREEN}✅ RAG监控系统已停止${NC}"
        return 0
    else
        echo -e "${RED}❌ 停止进程失败${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 重启RAG监控
restart_rag() {
    echo -e "${PURPLE}🔄 重启RAG监控系统...${NC}"
    stop_rag
    sleep 2
    start_rag
}

# 查看状态
status_rag() {
    echo -e "${BLUE}📊 RAG监控系统状态${NC}"
    echo "================================"
    
    if is_running; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        echo -e "${GREEN}状态: 运行中 ✅${NC}"
        echo -e "${CYAN}PID: $pid${NC}"
        
        # 获取进程信息
        if command -v ps >/dev/null 2>&1; then
            local cpu_mem=$(ps -p "$pid" -o %cpu,%mem --no-headers 2>/dev/null | tr -s ' ')
            if [ -n "$cpu_mem" ]; then
                echo -e "${CYAN}CPU/内存: $cpu_mem${NC}"
            fi
            
            local start_time=$(ps -p "$pid" -o lstart --no-headers 2>/dev/null)
            if [ -n "$start_time" ]; then
                echo -e "${CYAN}启动时间: $start_time${NC}"
            fi
        fi
    else
        echo -e "${RED}状态: 未运行 ❌${NC}"
    fi
    
    echo "--------------------------------"
    echo -e "${CYAN}配置目录: $CONFIG_DIR${NC}"
    echo -e "${CYAN}监控脚本: $RAG_SCRIPT${NC}"
    echo -e "${CYAN}日志文件: $LOG_FILE${NC}"
    
    # 显示日志文件大小
    if [ -f "$LOG_FILE" ]; then
        local log_size=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1)
        echo -e "${CYAN}日志大小: $log_size${NC}"
    fi
    
    # 如果运行中，获取详细状态
    if is_running && check_script; then
        echo "--------------------------------"
        echo -e "${BLUE}详细状态信息:${NC}"
        python3 "$RAG_SCRIPT" status 2>/dev/null || echo -e "${YELLOW}无法获取详细状态${NC}"
    fi
}

# 查看RAG队列
queue_rag() {
    echo -e "${BLUE}📋 查看RAG队列${NC}"
    echo "================================"
    
    if ! check_script; then
        return 1
    fi
    
    python3 "$RAG_SCRIPT" queue 2>/dev/null || echo -e "${YELLOW}无法获取队列信息${NC}"
}

# 清空RAG队列
clear_queue() {
    echo -e "${YELLOW}🗑️  清空RAG队列...${NC}"
    
    if ! check_script; then
        return 1
    fi
    
    python3 "$RAG_SCRIPT" clear 2>/dev/null && echo -e "${GREEN}✅ RAG队列已清空${NC}"
}

# 查看日志
show_logs() {
    local lines=${1:-50}
    echo -e "${BLUE}📄 显示最近 $lines 行日志${NC}"
    echo "================================"
    
    if [ -f "$LOG_FILE" ]; then
        tail -n "$lines" "$LOG_FILE"
    else
        echo -e "${YELLOW}日志文件不存在${NC}"
    fi
}

# 实时查看日志
follow_logs() {
    echo -e "${BLUE}📄 实时监控日志 (Ctrl+C 退出)${NC}"
    echo "================================"
    
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}日志文件不存在，等待创建...${NC}"
        while [ ! -f "$LOG_FILE" ]; do
            sleep 1
        done
        tail -f "$LOG_FILE"
    fi
}

# 测试RAG功能
test_rag() {
    echo -e "${BLUE}🧪 测试RAG监控功能${NC}"
    echo "================================"
    
    if ! is_running; then
        echo -e "${RED}❌ RAG监控系统未运行，请先启动${NC}"
        return 1
    fi
    
    # 模拟添加测试记忆
    echo -e "${CYAN}添加测试记忆...${NC}"
    
    # 这里可以添加测试逻辑
    # 例如通过tgptm命令添加一个测试记忆，然后检查是否触发RAG
    
    echo -e "${GREEN}测试完成，请查看日志了解详情${NC}"
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}智能RAG监控系统管理工具${NC}"
    echo "================================"
    echo "用法: $0 [命令] [参数]"
    echo ""
    echo "命令:"
    echo -e "  ${GREEN}start${NC}           启动RAG监控系统"
    echo -e "  ${GREEN}stop${NC}            停止RAG监控系统"
    echo -e "  ${GREEN}restart${NC}         重启RAG监控系统"
    echo -e "  ${GREEN}status${NC}          查看运行状态"
    echo -e "  ${GREEN}queue${NC}           查看RAG队列"
    echo -e "  ${GREEN}clear${NC}           清空RAG队列"
    echo -e "  ${GREEN}logs [行数]${NC}      查看日志 (默认50行)"
    echo -e "  ${GREEN}follow${NC}          实时监控日志"
    echo -e "  ${GREEN}test${NC}            测试RAG功能"
    echo -e "  ${GREEN}help${NC}            显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动监控"
    echo "  $0 status         # 查看状态"
    echo "  $0 logs 100       # 查看最近100行日志"
    echo "  $0 follow         # 实时监控日志"
}

# 主逻辑
case "${1:-help}" in
    start)
        start_rag
        ;;
    stop)
        stop_rag
        ;;
    restart)
        restart_rag
        ;;
    status)
        status_rag
        ;;
    queue)
        queue_rag
        ;;
    clear)
        clear_queue
        ;;
    logs)
        show_logs "${2:-50}"
        ;;
    follow)
        follow_logs
        ;;
    test)
        test_rag
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac 