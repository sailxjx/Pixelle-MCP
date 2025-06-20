#!/bin/bash

# 重启Chainlit服务脚本
# 配置端口号
PORT=9003

echo "🔄 正在重启Chainlit服务（端口：$PORT）..."

# 查找并终止已存在的chainlit进程
echo "🔍 查找已存在的chainlit进程..."

# 通过端口号查找并终止进程
PORT_PID=$(lsof -ti:$PORT)
if [ ! -z "$PORT_PID" ]; then
    echo "📍 发现端口$PORT上的进程: $PORT_PID"
    echo "🔪 正在终止端口$PORT上的进程..."
    kill -TERM $PORT_PID
    sleep 2
    # 如果进程仍然存在，强制终止
    if kill -0 $PORT_PID 2>/dev/null; then
        echo "⚡ 强制终止进程..."
        kill -KILL $PORT_PID
    fi
    echo "✅ 端口$PORT上的进程已终止"
else
    echo "ℹ️  端口$PORT上没有发现运行的进程"
fi

# 等待一段时间确保进程完全终止
echo "⏳ 等待进程完全终止..."
sleep 3

# 启动新的chainlit进程
echo "🚀 启动新的Chainlit服务（端口$PORT）..."

# 检查main.py是否存在
if [ ! -f "main.py" ]; then
    echo "❌ 错误: main.py文件不存在！"
    exit 1
fi

# 激活当前环境
source .venv/bin/activate

# 安装依赖（不修改lock文件）
~/.local/bin/uv sync --frozen

# 启动chainlit服务
nohup chainlit run main.py --port $PORT --host 0.0.0.0 > server.log 2>&1 &

# 获取新进程的PID
NEW_PID=$!
echo "✅ Chainlit服务已启动，PID: $NEW_PID"

# 等待一小会确保服务启动
sleep 2

# 检查服务是否正常启动
if kill -0 $NEW_PID 2>/dev/null; then
    echo "🎉 服务启动成功，日志输出到 server.log"
    echo "📋 可以使用 'tail -f server.log' 查看实时日志"
else
    echo "❌ 服务启动失败，请检查 server.log 日志"
    exit 1
fi
