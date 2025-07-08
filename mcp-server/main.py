import importlib
import json
import os
import shutil
from pathlib import Path

from pydantic import Field
from core import mcp, logger, mcp_tool
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

@mcp_tool(name="save_tool")
async def save_tool(
    workflow_url: str = Field(description="The workflow to save, must be a url"),
    uploaded_filename: str = Field(None, description="use file attachment name that user uploaded"),
):
    """
    Add or update a workflow to MCP tools.
    """
    try:
        # 下载文件到临时位置
        with download_files(workflow_url, auto_cleanup=False) as temp_workflow_path:
            # 确保目标目录存在
            os.makedirs(CUSTOM_WORKFLOW_DIR, exist_ok=True)
            
            # 确定最终文件名
            if uploaded_filename:
                # 使用用户上传的文件名
                final_filename = uploaded_filename
                # 如果文件名没有.json扩展名，添加它
                if not final_filename.endswith('.json'):
                    final_filename += '.json'
            else:
                # 如果没有提供文件名，使用临时文件名的基础名
                final_filename = Path(temp_workflow_path).name
            
            # 目标文件路径
            target_path = Path(CUSTOM_WORKFLOW_DIR) / final_filename
            
            # 移动文件到目标位置
            shutil.move(temp_workflow_path, target_path)
            logger.info(f"工作流文件已移动到: {target_path}")
            
            return json.dumps({
                "success": True,
                "message": f"工作流文件已保存，请刷新 MCP Tools 列表查看"
            }, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"保存工作流失败: {e}")
        return json.dumps({
            "success": False,
            "error": f"保存工作流失败: {str(e)}"
        }, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    try:
        # 启动MCP服务器
        print("🚀 启动 MCP 服务器...")
        print("📁 监听目录:", workflow_manager.workflows_dir)
        print("\n🌐 服务器启动中...")
        
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", 9002))
        mcp.run(transport="sse", port=port, host=host)
    finally:
        # 确保清理资源
        workflow_manager.cleanup()
