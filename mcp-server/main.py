import importlib
import os
from pathlib import Path
from core import mcp, logger

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

# 动态加载MCP各个子组件
load_modules("tools")
load_modules("resources")

if __name__ == "__main__":
    # 启动MCP服务器
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", 9002))
    mcp.run(transport="sse", port=port, host=host)
