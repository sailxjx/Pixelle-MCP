#!/bin/bash
set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"
LOG_DIR="$SCRIPT_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 颜色输出函数
print_info() {
    echo "🚀 $1"
}

print_success() {
    echo "✅ $1"
}

print_error() {
    echo "❌ $1"
}

print_warning() {
    echo "⚠️  $1"
}

# 检查uv是否安装
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "请先安装 uv"
        echo "安装方法: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

# 停止已有服务
stop_services() {
    if [ -f "$PID_FILE" ]; then
        print_info "正在停止已有服务..."
        while read -r line; do
            if [ -n "$line" ]; then
                IFS=' ' read -ra PIDS <<< "$line"
                for pid in "${PIDS[@]}"; do
                    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                        print_info "停止进程 $pid"
                        kill -TERM "$pid" 2>/dev/null || true
                        # 等待进程优雅退出
                        sleep 2
                        # 如果还没退出，强制杀死
                        if kill -0 "$pid" 2>/dev/null; then
                            print_warning "强制停止进程 $pid"
                            kill -KILL "$pid" 2>/dev/null || true
                        fi
                    fi
                done
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
        print_success "已停止所有服务"
    else
        print_info "没有找到运行中的服务"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "端口 $port 已被占用，尝试释放..."
        local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
        if [ -n "$pid" ]; then
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                kill -KILL "$pid" 2>/dev/null || true
            fi
        fi
    fi
}

# 启动单个服务
start_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    local daemon_mode=$4
    
    print_info "启动 $service_name..."
    cd "$SCRIPT_DIR/$service_dir"
    
    # 同步依赖
    uv sync
    
    # 检查并释放端口
    check_port "$port"
    
    if [ "$daemon_mode" = "true" ]; then
        # 后台运行模式，输出到日志文件
        nohup uv run main.py > "$LOG_DIR/$service_name.log" 2>&1 &
        local pid=$!
        echo $pid >> "$PID_FILE"
        print_success "$service_name 已在后台启动 (PID: $pid, 日志: $LOG_DIR/$service_name.log)"
    else
        # 前台运行模式
        uv run main.py &
        local pid=$!
        echo $pid >> "$PID_FILE"
        print_success "$service_name 已启动 (PID: $pid)"
    fi
    
    cd "$SCRIPT_DIR"
    
    # 等待服务启动
    sleep 3
    if ! kill -0 "$pid" 2>/dev/null; then
        print_error "$service_name 启动失败"
        return 1
    fi
}

# 启动所有服务
start_services() {
    local daemon_mode=$1
    
    print_info "启动 Pixelle MCP 服务..."
    
    # 清空PID文件
    > "$PID_FILE"
    
    # 启动base服务
    start_service "mcp-base" "mcp-base" "9001" "$daemon_mode"
    
    # 启动server服务  
    start_service "mcp-server" "mcp-server" "9002" "$daemon_mode"
    
    # 启动client服务
    start_service "mcp-client" "mcp-client" "9003" "$daemon_mode"
    
    print_success "所有服务启动完成!"
    echo "🌐 客户端: http://localhost:9003"
    echo "🗄️ 服务端: http://localhost:9002"  
    echo "🔧 基础服务: http://localhost:9001"
    
    if [ "$daemon_mode" = "true" ]; then
        echo "📋 日志目录: $LOG_DIR"
        echo "🔍 查看状态: $0 status"
        echo "🛑 停止服务: $0 stop"
    fi
}

# 查看服务状态
show_status() {
    print_info "检查服务状态..."
    
    if [ ! -f "$PID_FILE" ]; then
        print_info "没有运行中的服务"
        return
    fi
    
    local running_count=0
    local services=("mcp-base:9001" "mcp-server:9002" "mcp-client:9003")
    local line_num=0
    
    while read -r pid; do
        if [ -n "$pid" ] && [ "$line_num" -lt 3 ]; then
            local service_info="${services[$line_num]}"
            local service_name="${service_info%%:*}"
            local port="${service_info##*:}"
            
            if kill -0 "$pid" 2>/dev/null; then
                print_success "$service_name 运行中 (PID: $pid, 端口: $port)"
                running_count=$((running_count + 1))
            else
                print_error "$service_name 未运行"
            fi
            line_num=$((line_num + 1))
        fi
    done < "$PID_FILE"
    
    echo "运行中的服务数量: $running_count/3"
}

# 显示帮助信息
show_help() {
    echo "使用方法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  start           启动所有服务 (前台运行)"
    echo "  start --daemon  启动所有服务 (后台运行)"
    echo "  stop            停止所有服务"
    echo "  restart         重启所有服务"
    echo "  status          查看服务状态"
    echo "  logs [service]  查看服务日志"
    echo "  help            显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start --daemon   # 后台启动服务"
    echo "  $0 logs mcp-client  # 查看客户端日志"
    echo "  $0 restart          # 重启所有服务"
}

# 查看日志
show_logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_info "可用的服务日志:"
        ls -la "$LOG_DIR"/*.log 2>/dev/null || print_info "没有找到日志文件"
        return
    fi
    
    local log_file="$LOG_DIR/$service.log"
    if [ -f "$log_file" ]; then
        print_info "显示 $service 的日志 (Ctrl+C 退出):"
        tail -f "$log_file"
    else
        print_error "没有找到 $service 的日志文件: $log_file"
    fi
}

# 主逻辑
main() {
    local command=""
    local daemon_mode=false
    local remaining_args=()
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --daemon|-d)
                daemon_mode=true
                shift
                ;;
            start|stop|restart|status|logs|help|--help|-h)
                command="$1"
                shift
                # 收集剩余参数
                while [[ $# -gt 0 ]]; do
                    if [[ "$1" != "--daemon" && "$1" != "-d" ]]; then
                        remaining_args+=("$1")
                    else
                        daemon_mode=true
                    fi
                    shift
                done
                break
                ;;
            *)
                if [ -z "$command" ]; then
                    command="$1"
                fi
                shift
                ;;
        esac
    done
    
    # 如果没有指定命令，默认为start
    if [ -z "$command" ]; then
        command="start"
    fi
    
    case "$command" in
        start)
            check_uv
            stop_services
            if [ "$daemon_mode" = "true" ]; then
                start_services true
            else
                start_services false
                # 前台模式下等待任意服务退出
                print_info "按 Ctrl+C 停止所有服务"
                trap 'stop_services; exit 0' INT TERM
                wait
            fi
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_uv
            stop_services
            start_services true
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${remaining_args[0]}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"