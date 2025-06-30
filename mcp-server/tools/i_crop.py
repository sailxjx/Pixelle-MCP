from pydantic import Field
from core import mcp_tool, logger
from PIL import Image
from utils.upload_util import upload
from utils.file_util import download_files, create_temp_file

@mcp_tool
def i_crop(
    image_url: str = Field(description="The URL of the image to crop"),
):
    """Crop image to center of original"""
    try:
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
            
            # 创建临时文件保存裁剪后的图片（移出上一层嵌套）
            with create_temp_file('_cropped.jpg') as cropped_output_path:
                # 保存裁剪后的图片
                cropped_img.save(cropped_output_path, format='JPEG', quality=95)
                
                # 上传处理后的图片
                result_url = upload(cropped_output_path, 'cropped_image.jpg')
                
                logger.info(f"[crop] 原图尺寸: {original_width}x{original_height}")
                logger.info(f"[crop] 裁剪尺寸: {new_width}x{new_height}")
                logger.info(f"[crop] 结果URL: {result_url}")
                
                return {
                    "success": True,
                    "result": result_url,
                    "original_size": {"width": original_width, "height": original_height},
                    "cropped_size": {"width": new_width, "height": new_height}
                }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"裁剪图片时发生错误: {str(e)}"
        }