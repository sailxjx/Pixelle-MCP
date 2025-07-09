import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import json
import copy
import uuid
import time
import asyncio
import tempfile
import mimetypes
from urllib.parse import urlparse
from utils.os_util import get_root_path
from utils.workflow_parser import WorkflowParser, WorkflowMetadata  # 新增导入
from typing import Any, Optional, Dict, List, Tuple
from pydantic import BaseModel, Field

import aiohttp
from core import logger
from utils.file_util import download_files
from utils.upload_util import upload

# 配置变量
COMFYUI_BASE_URL = os.getenv('COMFYUI_BASE_URL', 'http://127.0.0.1:8188')
COMFYUI_API_KEY = os.getenv('COMFYUI_API_KEY')

WORKFLOW_DIR = get_root_path("tools/workflows")

# 需要特殊媒体上传处理的节点类型
MEDIA_UPLOAD_NODE_TYPES = {
    'LoadImage',
    'VHS_LoadAudioUpload', 
    'VHS_LoadVideo',
}


class ExecuteResult(BaseModel):
    """执行结果模型"""
    status: str = Field(description="执行状态")
    prompt_id: Optional[str] = Field(None, description="提示ID")
    duration: Optional[float] = Field(None, description="执行耗时（秒）")
    images: List[str] = Field(default_factory=list, description="图片URL列表")
    images_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="按变量名分组的图片")
    audios: List[str] = Field(default_factory=list, description="音频URL列表")
    audios_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="按变量名分组的音频")
    videos: List[str] = Field(default_factory=list, description="视频URL列表")
    videos_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="按变量名分组的视频")
    texts: List[str] = Field(default_factory=list, description="文本列表")
    texts_by_var: Dict[str, List[str]] = Field(default_factory=dict, description="按变量名分组的文本")
    outputs: Optional[Dict[str, Any]] = Field(None, description="原始输出")
    msg: Optional[str] = Field(None, description="消息")
    
    def to_llm_result(self) -> str:
        """转换为LLM可读的结果"""
        if self.status == "completed":
            output = "Generated successfully"
            
            def format_media_output(media_type: str, media_list: List[str], by_var_dict: Dict[str, List[str]]) -> str:
                """格式化媒体输出"""
                if by_var_dict and len(by_var_dict) > 1:
                    var_dict = {k: v[0] if v else None for k, v in by_var_dict.items()}
                    return f", {media_type}: {var_dict}"
                else:
                    return f", {media_type}: {media_list}"
            
            # 处理各种媒体类型
            for media_type in ["images", "audios", "videos", "texts"]:
                media_list = getattr(self, media_type)
                by_var_dict = getattr(self, f"{media_type}_by_var")
                if media_list:
                    output += format_media_output(media_type, media_list, by_var_dict)
            
            return output
        elif self.status == "error":
            return f"Generated failed, status: {self.status}, message: {self.msg}"
        else:
            return f"Generated failed, status: {self.status}"


def transfer_result_files(result: ExecuteResult) -> ExecuteResult:
    """转存结果文件到新的URL"""
    url_cache: Dict[str, str] = {}

    def transfer_urls(urls: List[str]) -> List[str]:
        # 去重，保留顺序
        unique_urls = []
        seen = set()
        for url in urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)
        
        # 下载并上传未缓存的url
        uncached_urls = [url for url in unique_urls if url not in url_cache]
        if uncached_urls:
            with download_files(uncached_urls) as temp_files:
                for temp_file, url in zip(temp_files, uncached_urls):
                    new_url = upload(temp_file)
                    url_cache[url] = new_url
        
        return [url_cache.get(url, url) for url in urls]

    def transfer_dict_urls(d: Dict[str, List[str]]) -> Dict[str, List[str]]:
        return {k: transfer_urls(v) for k, v in d.items()} if d else d

    # 构造新数据
    data = result.model_dump()
    for field in ["images", "audios", "videos"]:
        if data.get(field):
            data[field] = transfer_urls(data[field])
    for field in ["images_by_var", "audios_by_var", "videos_by_var"]:
        if data.get(field):
            data[field] = transfer_dict_urls(data[field])
    
    # texts是原生字符串，不需要转存
    for field in ["texts"]:
        if data.get(field):
            data[field] = data[field]
    for field in ["texts_by_var"]:
        if data.get(field):
            data[field] = data[field]
    
    return ExecuteResult(**data)


async def _load_workflow_from_url(url: str) -> Dict[str, Any]:
    """从URL加载工作流"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"下载工作流失败: HTTP {response.status}")
            text = await response.text()
            try:
                return json.loads(text)
            except Exception as e:
                raise Exception(f"解析工作流JSON失败: {e}")


async def _apply_param_mapping(workflow_data: Dict[str, Any], mapping: Any, param_value: Any):
    """根据参数映射应用单个参数"""
    node_id = mapping.node_id
    input_field = mapping.input_field
    node_class_type = mapping.node_class_type
    
    # 检查节点是否存在
    if node_id not in workflow_data:
        logger.warning(f"节点 {node_id} 不存在于工作流中")
        return
    
    node_data = workflow_data[node_id]
    
    # 确保inputs存在
    if "inputs" not in node_data:
        node_data["inputs"] = {}
    
    # 检查节点类型是否需要特殊媒体上传处理
    if node_class_type in MEDIA_UPLOAD_NODE_TYPES:
        await _handle_media_upload(node_data, input_field, param_value)
    else:
        # 常规参数设置
        await _set_node_param(node_data, input_field, param_value)


async def _handle_media_upload(node_data: Dict[str, Any], input_field: str, param_value: Any):
    """处理媒体上传"""
    # 确保inputs存在
    if "inputs" not in node_data:
        node_data["inputs"] = {}
    
    # 如果参数值是以http开头的URL，先上传媒体
    if isinstance(param_value, str) and param_value.startswith(('http://', 'https://')):
        try:
            # 上传媒体并获取上传后的媒体名
            media_value = await _upload_media_from_source(param_value)
            # 使用上传后的媒体名作为节点的输入值
            await _set_node_param(node_data, input_field, media_value)
            logger.info(f"媒体上传成功: {media_value}")
        except Exception as e:
            logger.error(f"媒体上传失败: {str(e)}")
            raise Exception(f"媒体上传失败: {str(e)}")
    else:
        # 直接使用参数值作为媒体名
        await _set_node_param(node_data, input_field, param_value)


async def _set_node_param(node_data: Dict[str, Any], input_field: str, param_value: Any):
    """设置节点参数"""
    # 确保inputs存在
    if "inputs" not in node_data:
        node_data["inputs"] = {}
    # 设置参数值
    node_data["inputs"][input_field] = param_value


async def _upload_media_from_source(media_url: str) -> str:
    """从URL上传媒体"""
    # 从URL下载媒体
    async with aiohttp.ClientSession() as session:
        async with session.get(media_url) as response:
            if response.status != 200:
                raise Exception(f"下载媒体失败: HTTP {response.status}")
            
            # 从URL提取文件名
            parsed_url = urlparse(media_url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"temp_media_{hash(media_url)}.jpg"
            
            # 获取媒体数据
            media_data = await response.read()
            
            # 保存到临时文件
            suffix = os.path.splitext(filename)[1] or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(media_data)
                temp_path = tmp.name
    
    try:
        # 上传临时文件到ComfyUI
        return await _upload_media(temp_path)
    finally:
        # 删除临时文件
        os.unlink(temp_path)


async def _upload_media(media_path: str) -> str:
    """上传媒体到ComfyUI"""
    # 读取媒体数据
    with open(media_path, 'rb') as f:
        media_data = f.read()
    
    # 提取文件名
    filename = os.path.basename(media_path)
    
    # 自动检测文件MIME类型
    mime_type = mimetypes.guess_type(filename)[0]
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    # 准备表单数据
    data = aiohttp.FormData()
    data.add_field('image', media_data, 
                   filename=filename, 
                   content_type=mime_type)
    
    # 上传媒体
    upload_url = f"{COMFYUI_BASE_URL}/upload/image"
    async with aiohttp.ClientSession() as session:
        async with session.post(upload_url, data=data) as response:
            if response.status != 200:
                raise Exception(f"上传媒体失败: HTTP {response.status}")
            
            # 获取上传结果
            result = await response.json()
            return result.get('name', '')


async def _apply_params_to_workflow(workflow_data: Dict[str, Any], metadata: WorkflowMetadata, params: Dict[str, Any]) -> Dict[str, Any]:
    """使用新解析器将参数应用到工作流"""
    workflow_data = copy.deepcopy(workflow_data)
    
    # 遍历所有参数映射
    for mapping in metadata.mapping_info.param_mappings:
        param_name = mapping.param_name
        
        # 检查参数是否存在
        if param_name in params:
            param_value = params[param_name]
            await _apply_param_mapping(workflow_data, mapping, param_value)
        else:
            # 使用默认值（如果存在）
            if param_name in metadata.params:
                param_info = metadata.params[param_name]
                if param_info.default is not None:
                    await _apply_param_mapping(workflow_data, mapping, param_info.default)
                elif param_info.required:
                    raise Exception(f"必填参数 '{param_name}' 缺失")
    
    return workflow_data


def _extract_output_nodes(metadata: WorkflowMetadata) -> Dict[str, str]:
    """从元数据提取输出节点及其输出变量名"""
    output_id_2_var = {}
    
    for output_mapping in metadata.mapping_info.output_mappings:
        output_id_2_var[output_mapping.node_id] = output_mapping.output_var
    
    return output_id_2_var


async def _queue_prompt(workflow: Dict[str, Any], client_id: str, prompt_ext_params: Optional[Dict[str, Any]] = None) -> str:
    """将工作流提交到队列"""
    prompt_data = {
        "prompt": workflow,
        "client_id": client_id
    }
    
    # 更新prompt_data与prompt_ext_params的所有参数
    if prompt_ext_params:
        prompt_data.update(prompt_ext_params)
    
    json_data = json.dumps(prompt_data)
    
    # 使用aiohttp发送请求
    prompt_url = f"{COMFYUI_BASE_URL}/prompt"
    async with aiohttp.ClientSession() as session:
        async with session.post(
                prompt_url, 
                data=json_data,
                headers={"Content-Type": "application/json"}
            ) as response:
            if response.status != 200:
                response_text = await response.text()
                raise Exception(f"提交工作流失败: [{response.status}] {response_text}")
            
            result = await response.json()
            prompt_id = result.get("prompt_id")
            if not prompt_id:
                raise Exception(f"获取prompt_id失败: {result}")
            logger.info(f"任务已提交: {prompt_id}")
            return prompt_id


def _split_media_by_suffix(node_output: Dict[str, Any], base_url: str) -> Tuple[List[str], List[str], List[str]]:
    """根据文件扩展名将媒体分为图片/视频/音频"""
    image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
    video_exts = {'.mp4', '.mov', '.avi', '.webm', '.gif'}
    audio_exts = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma', '.opus'}
    
    images = []
    videos = []
    audios = []
    
    for media_key in ("images", "gifs", "audio"):
        for media_data in node_output.get(media_key, []):
            filename = media_data.get("filename")
            subfolder = media_data.get("subfolder", "")
            media_type = media_data.get("type", "output")
            
            url = f"{base_url}/view?filename={filename}"
            if subfolder:
                url += f"&subfolder={subfolder}"
            if media_type:
                url += f"&type={media_type}"
            
            ext = os.path.splitext(filename)[1].lower()
            if ext in image_exts:
                images.append(url)
            elif ext in video_exts:
                videos.append(url)
            elif ext in audio_exts:
                audios.append(url)
    
    return images, videos, audios


def _map_outputs_by_var(output_id_2_var: Dict[str, str], output_id_2_media: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """根据变量名映射输出"""
    result = {}
    for node_id, media_data in output_id_2_media.items():
        # 如果有显式变量名则使用，否则使用node_id
        var_name = output_id_2_var.get(node_id, str(node_id))
        result[var_name] = media_data
    return result


def _extend_flat_list_from_dict(media_dict: Dict[str, List[str]]) -> List[str]:
    """将字典中的所有列表扁平化为单个列表"""
    flat = []
    for items in media_dict.values():
        flat.extend(items)
    return flat


async def _wait_for_results(prompt_id: str, timeout: Optional[int] = None, output_id_2_var: Optional[Dict[str, str]] = None) -> ExecuteResult:
    """等待工作流执行结果"""
    start_time = time.time()
    result = ExecuteResult(
        status="processing",
        prompt_id=prompt_id
    )

    # 获取基础URL
    base_url = COMFYUI_BASE_URL

    while True:
        # 检查超时
        if timeout is not None and timeout > 0:
            duration = time.time() - start_time
            if duration > timeout:
                logger.warning(f"超时: {duration} 秒")
                result.status = "timeout"
                result.duration = duration
                return result

        # 使用HTTP API获取历史记录
        try:
            history_url = f"{COMFYUI_BASE_URL}/history/{prompt_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(history_url) as response:
                    if response.status != 200:
                        await asyncio.sleep(1.0)
                        continue
                    history_data = await response.json()
                    if prompt_id not in history_data:
                        await asyncio.sleep(1.0)
                        continue
                    
                    prompt_history = history_data[prompt_id]
                    status = prompt_history.get("status")
                    if status and status.get("status_str") == "error":
                        result.status = "error"
                        messages = status.get("messages")
                        if messages:
                            errors = [
                                body.get("exception_message")
                                for type, body in messages
                                if type == "execution_error"
                            ]
                            error_message = "\n".join(errors)
                        else:
                            error_message = "未知错误"
                        result.msg = error_message
                        result.duration = time.time() - start_time
                        return result
                    
                    if "outputs" in prompt_history:
                        result.outputs = prompt_history["outputs"]
                        result.status = "completed"

                        # 按文件扩展名收集所有图片、视频、音频和文本输出
                        output_id_2_images = {}
                        output_id_2_videos = {}
                        output_id_2_audios = {}
                        output_id_2_texts = {}
                        
                        for node_id, node_output in prompt_history["outputs"].items():
                            images, videos, audios = _split_media_by_suffix(node_output, base_url)
                            if images:
                                output_id_2_images[node_id] = images
                            if videos:
                                output_id_2_videos[node_id] = videos
                            if audios:
                                output_id_2_audios[node_id] = audios
                            
                            # 收集文本输出
                            if "text" in node_output:
                                texts = node_output["text"]
                                if isinstance(texts, str):
                                    texts = [texts]
                                elif not isinstance(texts, list):
                                    texts = [str(texts)]
                                output_id_2_texts[node_id] = texts

                        # 如果有映射则按变量名映射
                        if output_id_2_images:
                            result.images_by_var = _map_outputs_by_var(output_id_2_var, output_id_2_images)
                            result.images = _extend_flat_list_from_dict(result.images_by_var)

                        if output_id_2_videos:
                            result.videos_by_var = _map_outputs_by_var(output_id_2_var, output_id_2_videos)
                            result.videos = _extend_flat_list_from_dict(result.videos_by_var)

                        if output_id_2_audios:
                            result.audios_by_var = _map_outputs_by_var(output_id_2_var, output_id_2_audios)
                            result.audios = _extend_flat_list_from_dict(result.audios_by_var)

                        # 处理texts/texts_by_var
                        if output_id_2_texts:
                            result.texts_by_var = _map_outputs_by_var(output_id_2_var, output_id_2_texts)
                            result.texts = _extend_flat_list_from_dict(result.texts_by_var)

                        # 由于ExecuteResult模型允许None值，不需要手动移除空字段
                        # Pydantic会自动处理None值的序列化

                        # 设置执行耗时
                        result.duration = time.time() - start_time
                        return result
        except Exception as e:
            logger.error(f"获取历史记录出错: {str(e)}")
        await asyncio.sleep(1.0)


def get_workflow_metadata(workflow_file: str) -> Optional[WorkflowMetadata]:
    """获取工作流元数据（使用新的解析器）"""
    parser = WorkflowParser()
    return parser.parse_workflow_file(workflow_file)

async def execute_workflow(workflow_file: str, params: Dict[str, Any] = None) -> ExecuteResult:
    """执行工作流"""
    try:
        if not os.path.exists(workflow_file):
            logger.error(f"工作流文件不存在: {workflow_file}")
            return ExecuteResult(status="error", msg=f"工作流文件不存在: {workflow_file}")
        
        # 获取工作流元数据
        metadata = get_workflow_metadata(workflow_file)
        if not metadata:
            return ExecuteResult(status="error", msg="无法解析工作流元数据")
        
        # 加载工作流JSON
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        if not workflow_data:
            return ExecuteResult(status="error", msg="工作流数据缺失")
        
        # 使用新的参数映射逻辑
        if params:
            workflow_data = await _apply_params_to_workflow(workflow_data, metadata, params)
        else:
            # 即使没有传入参数，也需要应用默认值
            workflow_data = await _apply_params_to_workflow(workflow_data, metadata, {})
        
        # 从元数据提取输出节点信息
        output_id_2_var = _extract_output_nodes(metadata)
        
        # 生成客户端ID
        client_id = str(uuid.uuid4())
        
        # 准备额外参数
        prompt_ext_params = {}
        if COMFYUI_API_KEY:
            prompt_ext_params = {
                "extra_data": {
                    "api_key_comfy_org": COMFYUI_API_KEY
                }
            }
        else:
            logger.warning("COMFYUI_API_KEY 未设置")
        
        # 提交工作流到ComfyUI队列
        try:
            prompt_id = await _queue_prompt(workflow_data, client_id, prompt_ext_params)
        except Exception as e:
            error_message = f"提交工作流失败: [{type(e)}] {str(e)}"
            logger.error(error_message)
            return ExecuteResult(status="error", msg=error_message)
        
        # 等待结果
        result = await _wait_for_results(prompt_id, None, output_id_2_var)
        
        # 转存结果文件
        result = transfer_result_files(result)
        return result
        
    except Exception as e:
        logger.error(f"执行工作流出错: {str(e)}", exc_info=True)
        return ExecuteResult(status="error", msg=str(e))


if __name__ == "__main__":
    import asyncio
    
    async def test_dreamshaper_workflow():
        # 首先解析工作流元数据
        workflow_file = "data/custom_workflows/test_t2v_by_dreamshaper.json"
        
        # 执行工作流
        print("⏳ 正在执行工作流...")
        result = await execute_workflow(workflow_file, {
            "prompt": "a beautiful anime girl with blue hair, masterpiece, high quality",
            "width": 768,
            "height": 512
        })
        
        print(f"✅ 执行完成! 状态: {result.model_dump_json(indent=2)}")
    # 运行测试
    asyncio.run(test_dreamshaper_workflow())