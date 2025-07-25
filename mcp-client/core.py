# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from yml_env_loader import load_yml_and_set_env
import logging
import os

# 优先加载config.yml并注入环境变量
load_yml_and_set_env("client")

# 日志配置
logger_level = logging.INFO
logging.basicConfig(
    level=logger_level,
    format='%(asctime)s- %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True  # 强制重新配置，覆盖已有配置
)

logger = logging.getLogger("PMC")
logger.setLevel(logger_level)

logging.getLogger("httpx").setLevel(logging.WARNING)

# 移除原有的.env加载逻辑
# 加载环境变量
# ENV_PATH = [
#     ".env",
# ]
# for env_path in ENV_PATH:
#     if os.path.exists(env_path):
#         load_dotenv(env_path, override=True)
#         logger.info(f"env file loaded: {env_path}")
#     else:
#         logger.warning(f"env file not found: {env_path}, skip loading")

if __name__ == "__main__":
    logger.info(os.getenv("ABC"))