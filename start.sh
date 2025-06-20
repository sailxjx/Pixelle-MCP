#!/bin/bash

# Pixel MCP 完整 Docker 启动脚本
echo "🚀 正在启动 Pixel MCP 完整服务 (Docker)..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p mcp-server/data/minio
mkdir -p mcp-client/data

# 检查环境变量文件
echo "🔍 检查环境变量文件..."
if [ ! -f "mcp-server/.env" ]; then
    echo "⚠️  mcp-server/.env 文件不存在，请确保已正确配置"
fi

if [ ! -f "mcp-client/.env" ]; then
    echo "⚠️  mcp-client/.env 文件不存在，将使用默认配置"
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.yml down

# 构建并启动服务
echo "🏗️  构建 Docker 镜像..."
docker-compose -f docker-compose.yml build

echo "🚀 启动所有服务..."
docker-compose -f docker-compose.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
if docker-compose -f docker-compose.yml ps | grep -q "Up"; then
    echo "✅ 所有服务已成功启动！"
    echo ""
    echo "🌐 访问地址："
    echo "  📱 MCP Client:  http://localhost:9003"
    echo "  🔧 MCP Server:  http://localhost:9002"
    echo "  📦 MinIO:       http://localhost:9001"
    echo ""
    echo "📋 管理命令："
    echo "  查看日志: docker-compose -f docker-compose.yml logs -f"
    echo "  停止服务: docker-compose -f docker-compose.yml down"
    echo "  重启服务: docker-compose -f docker-compose.yml restart"
else
    echo "❌ 服务启动失败，请检查日志："
    echo "docker-compose -f docker-compose.yml logs"
    exit 1
fi 