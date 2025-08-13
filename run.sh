#!/bin/bash
set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.pids"
LOG_DIR="$SCRIPT_DIR/logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Color output functions
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

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "Please install uv first"
        echo "Installation: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

# Stop existing services
stop_services() {
    if [ -f "$PID_FILE" ]; then
        print_info "Stopping existing services..."
        while read -r line; do
            if [ -n "$line" ]; then
                IFS=' ' read -ra PIDS <<< "$line"
                for pid in "${PIDS[@]}"; do
                    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                        print_info "Stopping process $pid"
                        kill -TERM "$pid" 2>/dev/null || true
                        # Wait for graceful exit
                        sleep 2
                        # Force kill if still running
                        if kill -0 "$pid" 2>/dev/null; then
                            print_warning "Force stopping process $pid"
                            kill -KILL "$pid" 2>/dev/null || true
                        fi
                    fi
                done
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
        print_success "All services stopped"
    else
        print_info "No running services found"
    fi
}

# Check if port is occupied
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port is occupied, attempting to release..."
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

# Start single service
start_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    local daemon_mode=$4
    
    print_info "Starting $service_name..."
    cd "$SCRIPT_DIR/$service_dir"
    
    # Sync dependencies
    uv sync
    
    # Check and release port
    check_port "$port"
    
    if [ "$daemon_mode" = "true" ]; then
        # Background mode, output to log file
        nohup uv run main.py > "$LOG_DIR/$service_name.log" 2>&1 &
        local pid=$!
        echo $pid >> "$PID_FILE"
        print_success "$service_name started in background (PID: $pid, Log: $LOG_DIR/$service_name.log)"
    else
        # Foreground mode
        uv run main.py &
        local pid=$!
        echo $pid >> "$PID_FILE"
        print_success "$service_name started (PID: $pid)"
    fi
    
    cd "$SCRIPT_DIR"
    
    # Wait for service to start
    sleep 3
    if ! kill -0 "$pid" 2>/dev/null; then
        print_error "$service_name failed to start"
        return 1
    fi
}

# Start specified services
start_services() {
    local daemon_mode=$1
    local services_to_start=$2
    
    # If no services specified, start all
    if [ -z "$services_to_start" ]; then
        services_to_start="base,server,client"
    fi
    
    print_info "Starting Pixelle MCP services: $services_to_start"
    
    # Don't clear PID file - append to it to keep track of all running services
    if [ ! -f "$PID_FILE" ]; then
        > "$PID_FILE"
    fi
    
    # Parse services and start them
    IFS=',' read -ra SERVICES <<< "$services_to_start"
    for service in "${SERVICES[@]}"; do
        case "$service" in
            base)
                start_service "mcp-base" "mcp-base" "9001" "$daemon_mode"
                echo "🔧 Base Service: http://localhost:9001/docs"
                ;;
            server)
                start_service "mcp-server" "mcp-server" "9002" "$daemon_mode"
                echo "🗄️ Server: http://localhost:9002/sse"
                ;;
            client)
                start_service "mcp-client" "mcp-client" "9003" "$daemon_mode"
                echo "🌐 Client: http://localhost:9003"
                ;;
            *)
                print_error "Unknown service: $service"
                print_info "Available services: base, server, client"
                ;;
        esac
    done
    
    print_success "Selected services started successfully!"
    
    if [ "$daemon_mode" = "true" ]; then
        echo "📋 Log directory: $LOG_DIR"
        echo "🔍 Check status: $0 status"
        echo "🛑 Stop services: $0 stop"
    fi
}

# Check service status
show_status() {
    print_info "Checking service status..."
    
    if [ ! -f "$PID_FILE" ]; then
        print_info "No running services"
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
                print_success "$service_name is running (PID: $pid, Port: $port)"
                running_count=$((running_count + 1))
            else
                print_error "$service_name is not running"
            fi
            line_num=$((line_num + 1))
        fi
    done < "$PID_FILE"
    
    echo "Running services: $running_count/3"
}


# Show help information
show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start [services]     Start specified services (default: all)"
    echo "  stop                 Stop all services"
    echo "  restart [services]   Restart specified services"
    echo "  status               Check service status"
    echo "  logs [service]       View service logs"
    echo "  help                 Show help information"
    echo ""
    echo "Options:"
    echo "  --daemon, -d         Run services in background"
    echo ""
    echo "Available services:"
    echo "  base                 Base service (port 9001)"
    echo "  server               Server service (port 9002)"
    echo "  client               Client service (port 9003)"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start all services in foreground"
    echo "  $0 start --daemon           # Start all services in background"
    echo "  $0 start base               # Start only base service"
    echo "  $0 start base,server        # Start base and server services"
    echo "  $0 start server,client -d   # Start server and client in background"
    echo "  $0 restart base             # Restart only base service"
    echo "  $0 logs mcp-server          # View server logs"
    echo "  $0 stop                     # Stop all services"
}

# View logs
show_logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_info "Available service logs:"
        ls -la "$LOG_DIR"/*.log 2>/dev/null || print_info "No log files found"
        return
    fi
    
    local log_file="$LOG_DIR/$service.log"
    if [ -f "$log_file" ]; then
        print_info "Showing $service logs (Ctrl+C to exit):"
        tail -f "$log_file"
    else
        print_error "Log file not found for $service: $log_file"
    fi
}

# Main logic
main() {
    local command=""
    local daemon_mode=false
    local remaining_args=()
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --daemon|-d)
                daemon_mode=true
                shift
                ;;
            start|stop|restart|status|logs|help|--help|-h)
                command="$1"
                shift
                # Collect remaining arguments
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
    
    # Default to start if no command specified
    if [ -z "$command" ]; then
        command="start"
    fi
    
    case "$command" in
        start)
            check_uv
            # Get the services list from remaining_args
            local services_list="${remaining_args[0]}"
            if [ "$daemon_mode" = "true" ]; then
                start_services true "$services_list"
            else
                start_services false "$services_list"
                # Wait for any service to exit in foreground mode
                print_info "Press Ctrl+C to stop services"
                trap 'stop_services; exit 0' INT TERM
                wait
            fi
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_uv
            # Get the services list from remaining_args
            local services_list="${remaining_args[0]}"
            stop_services
            start_services true "$services_list"
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
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"