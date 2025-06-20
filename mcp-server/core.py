from fastmcp import FastMCP
from dotenv import load_dotenv
import logging
import os

# 初始化MCP服务器
mcp = FastMCP("aigc-mcp")
mcp_tool = mcp.tool
mcp_resource = mcp.resource

# 日志配置
logger_level = logging.INFO
logging.basicConfig(
    level=logger_level,
    format='%(asctime)s- %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True  # 强制重新配置，覆盖已有配置
)

logger = logging.getLogger("AM")
logger.setLevel(logger_level)

# 加载环境变量
ENV_PATH = [
    ".env",
    ".env.local",
]
for env_path in ENV_PATH:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        logger.info(f"env file loaded: {env_path}")
    else:
        logger.warning(f"env file not found: {env_path}, skip loading")

if __name__ == "__main__":
    logger.info(os.getenv("ABC"))