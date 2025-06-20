from core import logger
from typing import Optional, List
from pydantic import BaseModel
import requests
import json
import os
import tempfile
import traceback
from datetime import datetime
import imghdr
from PIL import Image
import time
import io
import asyncio

from utils.os_util import get_data_path, save_base64_to_file

# Key池账号
OPENAI_API_KEY = os.getenv('GPT4_IMAGE_API_KEY')
OPENAI_IMAGE_EDIT_URL = 'https://pre-openai-keys.alibaba-inc.com/v1/images/edits'
PROXY_URL = ''

class GptImageEditResult(BaseModel):
    success: bool
    msg: str
    output_path: Optional[str] = None

def detect_image_type_and_fix(img_bytes: bytes, raw_fname: str, resp_ctype: str):
    """
    根据图片字节流、原始文件名和响应头content-type，返回合法的文件名和content-type。
    """
    # 优先用content-type
    img_type = None
    ctype = resp_ctype or ''
    if ctype in ("image/jpeg", "image/png", "image/webp"):
        img_type = ctype.split("/")[-1]
    else:
        # 用imghdr或PIL识别
        img_type = imghdr.what(None, h=img_bytes)
        if not img_type:
            try:
                img = Image.open(io.BytesIO(img_bytes))
                img_type = img.format.lower()
            except Exception:
                img_type = None
        if img_type == "jpeg":
            ctype = "image/jpeg"
        elif img_type == "png":
            ctype = "image/png"
        elif img_type == "webp":
            ctype = "image/webp"
        else:
            return None, None
    # 修正文件名后缀
    ext = f'.{img_type}' if not raw_fname.lower().endswith(f'.{img_type}') else ''
    fname = raw_fname if raw_fname.lower().endswith(f'.{img_type}') else raw_fname + ext
    return fname, ctype

def _prepare_save_directory(prompt: str) -> str:
    """准备保存目录并写入prompt文件"""
    now_str = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')[:-3]
    save_dir = get_data_path('gpt_image', now_str)
    os.makedirs(save_dir, exist_ok=True)
    prompt_path = os.path.join(save_dir, 'prompt.txt')
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
    return save_dir

def _process_image_bytes(image_bytes_list: List[bytes], filenames: List[str], 
                        content_types: List[str], save_dir: str, temp_files: List[str]) -> List[str]:
    """处理image_bytes_list，返回图片文件路径列表"""
    image_files = []
    for idx, img_bytes in enumerate(image_bytes_list):
        fname = filenames[idx] if filenames and idx < len(filenames) else f"input_{idx}.png"
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(fname)[-1] or '.png')
        temp_file.write(img_bytes)
        temp_file.close()
        temp_files.append(temp_file.name)
        image_files.append(temp_file.name)
        
        # 保存输入图片
        input_save_path = os.path.join(save_dir, f'input_{idx}{os.path.splitext(fname)[-1] or ".png"}')
        with open(input_save_path, 'wb') as f:
            f.write(img_bytes)
    
    return image_files

def _process_image_urls(image_urls: List[str], save_dir: str, temp_files: List[str]) -> List[str]:
    """处理image_urls，下载并返回图片文件路径列表"""
    image_files = []
    for idx, url in enumerate(image_urls):
        logger.info(f"[gpt_image_edit_by_curl] 正在下载图片: {url}")
        
        # 使用requests下载图片（下载很快，用requests即可）
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}")
            img_bytes = resp.content
        except Exception as e:
            raise Exception(f"下载图片异常: {url} - {str(e)}")
        
        raw_fname = os.path.basename(url.split('?')[0]) or f'input_{idx}'
        fname, ctype = detect_image_type_and_fix(img_bytes, raw_fname, resp.headers.get('Content-Type', ''))
        
        if not fname or not ctype:
            raise Exception(f"图片类型不支持: {raw_fname}")
        
        # 创建临时文件
        ext = os.path.splitext(fname)[-1]
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext or '.png')
        temp_file.write(img_bytes)
        temp_file.close()
        temp_files.append(temp_file.name)
        image_files.append(temp_file.name)
        
        # 保存输入图片
        input_save_path = os.path.join(save_dir, f'input_{idx}{ext or ".png"}')
        with open(input_save_path, 'wb') as f:
            f.write(img_bytes)
    
    return image_files

def _process_mask(mask_bytes: bytes, mask_filename: str, save_dir: str, 
                 temp_files: List[str], image_count: int) -> Optional[str]:
    """处理mask文件，返回mask文件路径"""
    if not mask_bytes:
        return None
    
    if image_count != 1:
        raise Exception("mask仅支持单图编辑")
    
    mask_fname = mask_filename or "mask.png"
    mask_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(mask_fname)[-1] or '.png')
    mask_temp_file.write(mask_bytes)
    mask_temp_file.close()
    temp_files.append(mask_temp_file.name)
    
    # 保存mask图片
    mask_save_path = os.path.join(save_dir, f'mask{os.path.splitext(mask_fname)[-1] or ".png"}')
    with open(mask_save_path, 'wb') as f:
        f.write(mask_bytes)
    
    return mask_temp_file.name

def _build_curl_command(prompt: str, image_files: List[str], mask_file: Optional[str]) -> List[str]:
    """构造curl命令"""
    command = [
        'curl',
        '-X', 'POST',
        OPENAI_IMAGE_EDIT_URL,
        '-H', f'Authorization: Bearer {OPENAI_API_KEY}',
        '-H', 'Connection: keep-alive',
        '--keepalive-time', '60',  # 每60秒发送keep-alive包
        '--connect-timeout', '30',
        '--max-time', '600'
    ]
    
    # 添加代理设置
    if PROXY_URL:
        command.extend(['--proxy', PROXY_URL])
    
    # 添加表单数据
    command.extend(['-F', f'model=gpt-image-1'])
    command.extend(['-F', f'prompt={prompt}'])
    
    # 添加图片文件
    for image_file in image_files:
        command.extend(['-F', f'image[]=@{image_file}'])
    
    # 添加mask文件
    if mask_file:
        command.extend(['-F', f'mask=@{mask_file}'])
    
    return command

async def _execute_curl_request(command: List[str]) -> tuple[int, str, str, float]:
    """执行curl请求，返回(返回码, 标准输出, 标准错误, 耗时)"""
    logger.info(f"[gpt_image_edit_by_curl] 正在执行curl命令")
    
    # 记录请求开始时间
    request_start_time = time.time()
    logger.info(f"[gpt_image_edit_by_curl] 请求开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 使用异步subprocess执行curl命令
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()
    
    # 记录请求完成时间
    request_end_time = time.time()
    request_duration = request_end_time - request_start_time
    logger.info(f"[gpt_image_edit_by_curl] 请求完成，耗时: {request_duration:.2f}秒")
    
    return proc.returncode, stdout.decode('utf-8'), stderr.decode('utf-8'), request_duration

def _process_response(response_text: str, save_dir: str) -> List[str]:
    """处理API响应并上传到OSS，返回OSS URL列表"""
    logger.info(f"[gpt_image_edit_by_curl] 响应长度: {len(response_text)}字符")
    
    # 解析响应
    try:
        resp_json = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise Exception(f"响应JSON解析失败: {str(e)}, 响应内容: {response_text[:500]}")
    
    # 处理API错误
    if 'error' in resp_json:
        raise Exception(f"OpenAI API错误: {resp_json['error']}")
    
    # 支持多图返回
    data_list = resp_json.get('data', [])
    image_paths = []
    for idx, item in enumerate(data_list):
        b64_data = item.get('b64_json')
        if not b64_data:
            continue
        image_path = get_data_path(save_dir, f'output_{idx}.png')
        save_base64_to_file(b64_data, image_path)
        image_paths.append(image_path)
    
    if not image_paths:
        raise Exception("OpenAI未返回图片数据")
    
    return image_paths

def _cleanup_temp_files(temp_files: List[str]):
    """清理临时文件"""
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except Exception:
            pass

async def gpt_image_edit_by_curl(
    prompt: str,
    image_bytes_list: List[bytes] = None,
    filenames: List[str] = None,
    content_types: List[str] = None,
    image_urls: List[str] = None,
    mask_bytes: bytes = None,
    mask_filename: str = None,
    mask_content_type: str = None,
) -> GptImageEditResult:
    """
    使用curl调用OpenAI图片编辑API，解决keep-alive问题
    """
    logger.info(f"[gpt_image_edit_by_curl] 开始, prompt={prompt}, filenames={filenames}, image_urls={image_urls}, mask={mask_filename}")
    
    temp_files = []  # 用于跟踪需要清理的临时文件
    
    try:
        # 1. 准备保存目录
        save_dir = _prepare_save_directory(prompt)
        
        # 2. 处理图片来源
        image_files = []
        if image_bytes_list:
            image_files = _process_image_bytes(image_bytes_list, filenames, content_types, save_dir, temp_files)
        elif image_urls:
            image_files = _process_image_urls(image_urls, save_dir, temp_files)
        else:
            msg = "必须提供image_bytes_list或image_urls"
            logger.error(f"[gpt_image_edit_by_curl] 错误: {msg}")
            return GptImageEditResult(success=False, msg=msg, output_path=None)
        
        # 3. 处理mask
        mask_file = _process_mask(mask_bytes, mask_filename, save_dir, temp_files, len(image_files))
        
        # 4. 构造并执行curl命令
        command = _build_curl_command(prompt, image_files, mask_file)
        return_code, stdout, stderr, duration = await _execute_curl_request(command)
        
        if return_code != 0:
            msg = f"curl执行失败: {stderr}"
            logger.error(f"[gpt_image_edit_by_curl] 错误: {msg}")
            return GptImageEditResult(success=False, msg=msg, output_path=None)
        
        # 5. 处理响应
        paths = _process_response(stdout, save_dir)
        
        logger.info(f"[gpt_image_edit_by_curl] 处理成功: {paths}")
        return GptImageEditResult(success=True, msg="ok", output_path=paths if len(paths) > 1 else paths[0])
        
    except Exception as e:
        # 日志中记录完整错误信息
        full_msg = f"curl图片编辑请求失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"[gpt_image_edit_by_curl] 异常: {full_msg}")
        
        # 前端只返回友好的错误信息，不包含堆栈
        user_msg = f"curl图片编辑请求失败: {str(e)}"
        return GptImageEditResult(success=False, msg=user_msg, output_path=None)
    finally:
        # 6. 清理临时文件
        _cleanup_temp_files(temp_files)


if __name__ == "__main__":
    # 便于本地测试
    import asyncio
    
    async def test():
        prompt = "转化为齐白石风格"
        imageUrl = "https://img1.baidu.com/it/u=4243742111,2598308111&fm=253&fmt=auto&app=138&f=JPEG?w=800&h=1152"
        start_time = time.time()
        result = await gpt_image_edit_by_curl(prompt, image_urls=[imageUrl])
        end_time = time.time()
        print(result) 
        print(f"图片编辑请求耗时: {int(end_time - start_time)}秒")
    
    asyncio.run(test())