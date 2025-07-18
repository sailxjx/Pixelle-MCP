FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml ./
COPY uv.lock* ./

# 安装Python依赖
RUN uv sync --frozen

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/files

# 暴露端口
EXPOSE 9001

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# 启动应用
CMD ["uv", "run", "main.py"] 