import importlib
import json
import os
import shutil
from pathlib import Path

from pydantic import Field
from core import mcp, logger
from manager.workflow_manager import workflow_manager, CUSTOM_WORKFLOW_DIR
from utils.file_util import download_files


def load_modules(module_name: str):
    """动态加载tools文件夹中的所有工具"""
    tools_dir = Path(module_name)
    
    if not tools_dir.exists():
        logger.error(f"{module_name} directory not found!")
        return
    
    # 遍历tools文件夹中的所有Python文件
    for py_file in tools_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue
            
        module_name_with_ext = f"{module_name}.{py_file.stem}"
        try:
            # 动态导入模块
            importlib.import_module(module_name_with_ext)
            logger.info(f"Loaded module from {module_name_with_ext}.")
        except Exception as e:
            logger.error(f"Error loading {module_name_with_ext} from {module_name}: {e}")

# 动态加载其他资源
load_modules("resources")
load_modules("tools")

if __name__ == "__main__":
    # 启动MCP服务器
    print("🚀 启动 MCP 服务器...")
    print("📁 监听目录:", workflow_manager.workflows_dir)
    print("\n🌐 服务器启动中...")
    
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", 9002))
    mcp.run(transport="sse", port=port, host=host)
