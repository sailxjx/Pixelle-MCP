from PIL import Image
from utils.file_util import download_files


def detect_image_aspect_ratio(image_url: str) -> str:
    """
    从图片URL检测图片的宽高比
    
    Args:
        image_url: 图片的URL
        
    Returns:
        str: 宽高比字符串，如 "1:1", "16:9", "9:16", "4:3", "3:4"
    """
    try:
        with download_files(image_url) as temp_file_path:
            with Image.open(temp_file_path) as img:
                width, height = img.size
                
                # 计算宽高比
                ratio = width / height
                
                # 根据比例返回对应的宽高比字符串
                if abs(ratio - 1.0) < 0.1:  # 接近正方形
                    return "1:1"
                elif abs(ratio - 16/9) < 0.1:  # 接近16:9
                    return "16:9"
                elif abs(ratio - 9/16) < 0.1:  # 接近9:16
                    return "9:16"
                elif abs(ratio - 4/3) < 0.1:  # 接近4:3
                    return "4:3"
                elif abs(ratio - 3/4) < 0.1:  # 接近3:4
                    return "3:4"
                else:
                    # 根据宽高比判断是横向还是纵向
                    if ratio > 1:
                        return "16:9"  # 默认横向宽高比
                    else:
                        return "9:16"  # 默认纵向宽高比
                        
    except Exception as e:
        # 如果检测失败，返回默认值
        return "1:1" 