#!/bin/bash

# Docker化MCP服务重启脚本
echo "🔄 正在重启MCP服务..."

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ 错误: Docker服务未运行，请先启动Docker！"
    exit 1
fi

# 先构建新镜像（服务继续运行）
echo "🔨 构建新镜像..."
if ! docker-compose build; then
    echo "❌ 构建失败！请检查Dockerfile和依赖项"
    echo "💡 可以运行 'docker-compose build --no-cache' 尝试清理缓存重新构建"
    exit 1
fi
echo "✅ 镜像构建成功"

# 等构建完成后快速替换
echo "🛑 停止现有容器..."
if ! docker-compose down; then
    echo "❌ 停止容器失败！"
    exit 1
fi

echo "🚀 启动新容器..."
if ! docker-compose up -d; then
    echo "❌ 启动容器失败！"
    echo "🔧 尝试诊断问题..."
    
    # 尝试显示错误日志
    echo "📋 错误日志："
    docker-compose logs --tail=100
    exit 1
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 检查容器状态
echo "📋 检查容器状态..."
if docker-compose ps; then
    # 检查是否有容器在运行
    if docker-compose ps | grep -q "Up"; then
        echo "✅ MCP服务已重启完成！"
        echo "📋 可以使用 'docker-compose logs -f' 查看实时日志"
    else
        echo "⚠️  容器已启动但可能存在问题，请查看日志："
        docker-compose logs --tail=100
        exit 1
    fi
else
    echo "❌ 无法获取容器状态，请手动检查"
    exit 1
fi
