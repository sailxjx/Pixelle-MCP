import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from core import mcp_tool, logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.os_util import get_data_path
from utils.workflow_parser import WorkflowParser, WorkflowMetadata
from utils.comfyui_util import execute_workflow_v2

CUSTOM_WORKFLOW_DIR = get_data_path("custom_workflows")
os.makedirs(CUSTOM_WORKFLOW_DIR, exist_ok=True)

class WorkflowManager:
    """工作流管理器，支持动态加载和热更新"""
    
    def __init__(self, workflows_dir: str = CUSTOM_WORKFLOW_DIR):
        self.workflows_dir = Path(workflows_dir)
        self.loaded_workflows = {}  # 跟踪已加载的工作流 {workflow_name: workflow_info}
        self.setup_file_watcher()
        
    def setup_file_watcher(self):
        """设置文件监听器"""
        self.observer = Observer()
        self.observer.schedule(
            WorkflowEventHandler(self),
            str(self.workflows_dir),
            recursive=False
        )
        self.observer.start()
        logger.info(f"开始监听工作流目录: {self.workflows_dir}")
    
    def parse_workflow_metadata(self, workflow_path: Path) -> Optional[WorkflowMetadata]:
        """使用新的工作流解析器解析工作流元数据"""
        try:
            parser = WorkflowParser()
            metadata = parser.parse_workflow_file(str(workflow_path))
            return metadata
        except Exception as e:
            logger.error(f"解析工作流元数据失败 {workflow_path}: {e}")
            return None
    
    def _generate_params_str(self, params: Dict[str, Any]) -> str:
        """生成函数参数字符串"""
        # 分离必需参数和可选参数，确保参数顺序正确
        required_params = []
        optional_params = []
        
        for param_name, param in params.items():
            # 直接使用用户提供的description
            description = param.description or ''
            
            # 生成 Field 参数列表
            field_args = [f"description={repr(description)}"]
            if param.default is not None:
                field_args.append(f"default={repr(param.default)}")
            
            # 生成完整的参数定义
            param_str = f"{param_name}: {param.type} = Field({', '.join(field_args)})"
            
            # 根据是否有默认值分类
            if param.default is not None:
                optional_params.append(param_str)
            else:
                required_params.append(param_str)
        
        # 必需参数在前，可选参数在后
        return ", ".join(required_params + optional_params)
    
    def _generate_workflow_function(self, title: str, params_str: str, workflow_path: Path, description: Optional[str] = None) -> str:
        """生成工作流执行函数代码"""
        # 根据是否有description生成docstring
        if description:
            docstring_part = f'''    """
    {description}
    """
'''
        else:
            docstring_part = ""
        
        # 从路径中提取文件名（不含扩展名）用于错误日志
        workflow_name = Path(workflow_path).stem
        
        # 生成完整的函数定义
        return f'''async def {title}({params_str}):
{docstring_part}    try:
        # 获取传入的参数（排除特殊参数）
        params = {{k: v for k, v in locals().items() if not k.startswith('_')}}
        
        # 执行工作流
        result = await execute_workflow_v2("{workflow_path}", params)
        
        # 转换结果格式为LLM友好的格式
        if result.status == "completed":
            return result.to_llm_result()
        else:
            return f"工作流执行失败: {{result.msg or result.status}}"
            
    except Exception as e:
        logger.error(f"工作流执行失败 {workflow_name}: {{e}}")
        return f"工作流执行异常: {{str(e)}}"
'''
    
    def _register_workflow(self, workflow_path: Path, workflow_handler, metadata: WorkflowMetadata) -> None:
        """注册并记录工作流"""
        # 如果已存在同名工作流，先移除
        if workflow_path.stem in self.loaded_workflows:
            self.unload_workflow(workflow_path.stem)
        
        # 注册为MCP工具
        mcp_tool(workflow_handler)
        
        # 记录工作流信息
        self.loaded_workflows[workflow_path.stem] = {
            "function": workflow_handler,
            "metadata": metadata.model_dump(),
            "file_path": str(workflow_path),
            "loaded_at": f"{__import__('datetime').datetime.now()}"
        }
        
        logger.info(f"成功加载工作流: {workflow_path.stem}")
    
    def _save_workflow_if_needed(self, workflow_path: Path, title: str) -> Path:
        """如果需要，保存工作流文件到工作流目录"""
        target_workflow_path = self.workflows_dir / f"{title}.json"
        
        if not target_workflow_path.exists():
            try:
                # 确保工作流目录存在
                self.workflows_dir.mkdir(parents=True, exist_ok=True)
                
                # 复制工作流文件到工作流目录
                import shutil
                shutil.copy2(workflow_path, target_workflow_path)
                logger.info(f"工作流文件已保存到: {target_workflow_path}")
                
                return target_workflow_path
            except Exception as e:
                logger.warning(f"保存工作流文件失败: {e}")
        
        return workflow_path

    def load_workflow(self, workflow_path: Path | str, default_tool_name: str = None, save_workflow_if_not_exists: bool = True) -> Dict:
        """加载单个工作流
        
        Args:
            workflow_path: 工作流文件路径
            default_tool_name: 默认工具名称（当工作流中未指定title时使用）
            save_workflow_if_not_exists: 是否将工作流文件保存到工作流目录（如果目标文件不存在）
        """
        try:
            if isinstance(workflow_path, str):
                workflow_path = Path(workflow_path)
            
            # 检查文件是否存在
            if not workflow_path.exists():
                return {
                    "success": False,
                    "error": f"工作流文件不存在: {workflow_path}"
                }
            
            # 使用新的解析器解析工作流元数据
            metadata = self.parse_workflow_metadata(workflow_path)
            if not metadata:
                return {
                    "success": False,
                    "error": f"无法解析工作流元数据: {workflow_path}"
                }

            # 创建工具处理函数的参数列表
            title = metadata.title or default_tool_name
            
            if not title:
                return {
                    "success": False,
                    "error": f"工作流中未找到有效的工具名称"
                }
            
            # 如果需要，保存工作流文件到工作流目录
            if save_workflow_if_not_exists:
                workflow_path = self._save_workflow_if_needed(workflow_path, title)
            
            # 生成参数字符串
            params_str = self._generate_params_str(metadata.params)
            
            # 创建工具处理函数
            exec_globals = {}
            exec_locals = {}
            
            # 生成工作流执行函数
            func_def = self._generate_workflow_function(title, params_str, workflow_path, metadata.description)
            # 执行函数定义
            exec(func_def, {
                "metadata": metadata, 
                "logger": logger, 
                "Field": Field,
                "execute_workflow_v2": execute_workflow_v2
            }, exec_locals)
            workflow_handler = exec_locals[title]
            
            # 注册并记录工作流
            self._register_workflow(workflow_path, workflow_handler, metadata)
            
            return {
                "success": True,
                "workflow": workflow_path.stem,
                "metadata": metadata.model_dump(),
                "message": f"工作流 '{workflow_path.stem}' 已成功加载"
            }
            
        except Exception as e:
            logger.error(f"加载工作流失败 {workflow_path}: {e}")
            return {
                "success": False,
                "error": f"加载工作流失败: {str(e)}"
            }
            
    
    def unload_workflow(self, workflow_name: str) -> Dict:
        """卸载工作流"""
        if workflow_name not in self.loaded_workflows:
            return {
                "success": False,
                "error": f"工作流 '{workflow_name}' 不存在或未加载"
            }
        
        try:
            # 获取工作流信息
            workflow_info = self.loaded_workflows[workflow_name]
            
            # 从记录中删除
            del self.loaded_workflows[workflow_name]
            
            logger.info(f"成功卸载工作流: {workflow_name}")
            
            return {
                "success": True,
                "workflow": workflow_name,
                "message": f"工作流 '{workflow_name}' 已卸载"
            }
                
        except Exception as e:
            logger.error(f"卸载工作流失败 {workflow_name}: {e}")
            return {
                "success": False,
                "error": f"卸载工作流失败: {str(e)}"
            }
    
    def reload_workflow(self, workflow_name: str) -> Dict:
        """重新加载工作流"""
        if workflow_name not in self.loaded_workflows:
            return {
                "success": False,
                "error": f"工作流 '{workflow_name}' 不存在或未加载"
            }
        
        try:
            # 获取工作流文件路径
            workflow_path = Path(self.loaded_workflows[workflow_name]["file_path"])
            
            # 重新加载
            return self.load_workflow(workflow_path)
            
        except Exception as e:
            logger.error(f"重新加载工作流失败 {workflow_name}: {e}")
            return {
                "success": False,
                "error": f"重新加载工作流失败: {str(e)}"
            }
    
    def load_all_workflows(self) -> Dict:
        """加载所有工作流"""
        results = {
            "success": [],
            "failed": []
        }
        
        # 确保目录存在
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载所有JSON文件
        for json_file in self.workflows_dir.glob("*.json"):
            result = self.load_workflow(json_file)
            if result["success"]:
                results["success"].append(result["workflow"])
            else:
                results["failed"].append({
                    "file": json_file.name,
                    "error": result["error"]
                })
        
        return results
    
    def get_workflow_status(self) -> Dict:
        """获取所有工作流状态"""
        return {
            "total_loaded": len(self.loaded_workflows),
            "workflows": {
                name: {
                    "metadata": info["metadata"],
                    "loaded_at": info["loaded_at"]
                }
                for name, info in self.loaded_workflows.items()
            }
        }
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()

class WorkflowEventHandler(FileSystemEventHandler):
    """工作流文件变化事件处理器"""
    
    def __init__(self, manager: WorkflowManager):
        self.manager = manager
        self._last_modified_time = {}
    
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.json'):
            return
        
        logger.info(f"检测到新工作流文件: {event.src_path}")
        self.manager.load_workflow(Path(event.src_path))
    
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.json'):
            return
            
        # 防止重复触发
        current_time = time.time()
        if event.src_path in self._last_modified_time:
            if current_time - self._last_modified_time[event.src_path] < 1:  # 1秒内的修改忽略
                return
        self._last_modified_time[event.src_path] = current_time
        
        logger.info(f"检测到工作流文件修改: {event.src_path}")
        self.manager.load_workflow(Path(event.src_path))
    
    def on_deleted(self, event):
        if event.is_directory or not event.src_path.endswith('.json'):
            return
        
        workflow_name = Path(event.src_path).stem
        if workflow_name in self.manager.loaded_workflows:
            logger.info(f"检测到工作流文件删除: {event.src_path}")
            self.manager.unload_workflow(workflow_name)

# 创建工作流管理器实例
workflow_manager = WorkflowManager()

# 初始加载所有工作流
load_results = workflow_manager.load_all_workflows()
logger.info(f"初始工作流加载结果: {load_results}")

# 导出模块级别的变量和实例
__all__ = ['workflow_manager', 'WorkflowManager', 'CUSTOM_WORKFLOW_DIR'] 