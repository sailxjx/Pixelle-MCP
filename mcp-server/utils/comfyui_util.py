from pydantic import BaseModel, Field
from typing import Any, Optional
from core import logger
import requests
import os
from utils.file_util import download_files
from utils.upload_util import upload

COMFYUI_BASE_URL = os.getenv('COMFYUI_BASE_URL')
COMFYUI_API_KEY = os.getenv('COMFYUI_API_KEY')


class ExecuteResult(BaseModel):
    status: str = Field(description="The status of the execution")
    prompt_id: Optional[str] = Field(None, description="The prompt id of the execution")
    images: Optional[list[str]] = Field(None, description="The images of the execution")
    images_by_var: Optional[dict[str, list[str]]] = Field(None, description="The images grouped by variables name")
    audios: Optional[list[str]] = Field(None, description="The audio of the execution")
    audios_by_var: Optional[dict[str, list[str]]] = Field(None, description="The audios grouped by variables name")
    videos: Optional[list[str]] = Field(None, description="The video of the execution")
    videos_by_var: Optional[dict[str, list[str]]] = Field(None, description="The videos grouped by variables name")
    outputs: Optional[dict[str, Any]] = Field(None, description="The outputs of the execution")
    msg: Optional[str] = Field(None, description="The message of the execution")
    
    def to_llm_result(self) -> str:
        if self.status == "completed":
            output = "Generated successfully, "
            if self.images:
                output += f"images: {self.images}"
            if self.audios:
                output += f"audios: {self.audios}"
            if self.videos:
                output += f"videos: {self.videos}"
            return output
        elif self.status == "error":
            return f"Generation failed, status: {self.status}, msg: {self.msg}"
        else:
            return f"Generation failed, status: {self.status}"

def transfer_result_files(result: ExecuteResult) -> ExecuteResult:
    """
    将 ExecuteResult 中的 url 字段（images、audios、videos 及 *_by_var）转存为新 url。
    优化：url 去重，避免重复下载/上传。
    """
    url_cache: dict[str, str] = {}

    def transfer_urls(urls: list[str]) -> list[str]:
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
        # 返回原顺序的转存url
        return [url_cache.get(url, url) for url in urls]

    def transfer_dict_urls(d: dict[str, list[str]]) -> dict[str, list[str]]:
        return {k: transfer_urls(v) for k, v in d.items()} if d else d

    # 构造新数据
    data = result.model_dump()
    for field in ["images", "audios", "videos"]:
        if data.get(field):
            data[field] = transfer_urls(data[field])
    for field in ["images_by_var", "audios_by_var", "videos_by_var"]:
        if data.get(field):
            data[field] = transfer_dict_urls(data[field])
    return ExecuteResult(**data)

def execute_workflow(workflow: str, params: dict=None) -> ExecuteResult:
    api_url = f"{COMFYUI_BASE_URL}/oneapi/v1/execute"
    payload = {
        "workflow": workflow,
        "params": params,
    }
    if COMFYUI_API_KEY:
        prompt_ext_params = {
            "extra_data": {
                "api_key_comfy_org": COMFYUI_API_KEY
            }
        }
        payload['prompt_ext_params'] = prompt_ext_params
    else:
        logger.warning("COMFYUI_API_KEY is not set")
    
    try:
        logger.info(f"Executing workflow: {workflow}")
        response = requests.post(api_url, json=payload)
        data = response.json()
        error = data.get('error')
        if error:
            return ExecuteResult(status="error", msg=error)
        
        result = ExecuteResult(**data)
        result = transfer_result_files(result)
        return result
    except Exception as e:
        logger.error(f"Error executing workflow: {e}", exc_info=True)
        return ExecuteResult(status="error", msg=str(e))


if __name__ == "__main__":
    result = execute_workflow("flux_turbo.json", {
        "prompt": "a cute girl",
    })
    print(result.model_dump_json(indent=2))
