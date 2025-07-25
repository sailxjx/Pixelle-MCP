# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from typing import Callable
from fastmcp import FastMCP
from yml_env_loader import load_yml_and_set_env
import logging
import os

# 优先加载config.yml并注入环境变量
load_yml_and_set_env("server")

# 初始化MCP服务器
mcp = FastMCP(
    name="pixelle-mcp",
    on_duplicate_tools="replace",
)

# 日志配置
logger_level = logging.INFO
logging.basicConfig(
    level=logger_level,
    format='%(asctime)s- %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True  # 强制重新配置，覆盖已有配置
)

logger = logging.getLogger("PMS")
logger.setLevel(logger_level)

if __name__ == "__main__":
    logger.info(os.getenv("ABC"))