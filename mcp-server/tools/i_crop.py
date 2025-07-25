# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import json
from pydantic import Field
from core import mcp, logger
from PIL import Image
from utils.file_uploader import upload
from utils.file_util import download_files, create_temp_file

@mcp.tool
async def i_crop(
    image_url: str = Field(description="The URL of the image to crop"),
):
    """Crop image to center of original"""
    # 使用上下文管理器下载图片
    with download_files(image_url, '.jpg') as temp_image_path:
        # 打开图片并处理
        with Image.open(temp_image_path) as img:
            # 获取原图尺寸
            original_width, original_height = img.size
            
            # 计算新的尺寸（原图的一半）
            new_width = original_width // 2
            new_height = original_height // 2
            
            # 计算居中裁剪的坐标
            left = (original_width - new_width) // 2
            top = (original_height - new_height) // 2
            right = left + new_width
            bottom = top + new_height
            
            # 进行裁剪
            cropped_img = img.crop((left, top, right, bottom))
            
            # 如果图片是RGBA模式，需要转换为RGB模式才能保存为JPEG
            if cropped_img.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', cropped_img.size, (255, 255, 255))
                # 将RGBA图片粘贴到白色背景上
                background.paste(cropped_img, mask=cropped_img.split()[-1])  # 使用alpha通道作为mask
                cropped_img = background
            elif cropped_img.mode != 'RGB':
                # 其他模式也转换为RGB
                cropped_img = cropped_img.convert('RGB')
        
        # 创建临时文件保存裁剪后的图片（移出上一层嵌套）
        with create_temp_file('_cropped.jpg') as cropped_output_path:
            # 保存裁剪后的图片
            cropped_img.save(cropped_output_path, format='JPEG', quality=95)
            
            # 上传处理后的图片
            result_url = upload(cropped_output_path, 'cropped_image.jpg')
            
            logger.info(f"[crop] 原图尺寸: {original_width}x{original_height}")
            logger.info(f"[crop] 裁剪尺寸: {new_width}x{new_height}")
            logger.info(f"[crop] 结果URL: {result_url}")

            return f"原图尺寸: {original_width}x{original_height}\n裁剪尺寸: {new_width}x{new_height}\n结果URL: {result_url}"
    