import boto3
from botocore.client import Config
from abc import ABC, abstractmethod
from typing import Union, Tuple
import os
from pathlib import Path
import requests
from urllib.parse import urlparse
import uuid
import mimetypes
from core import logger
import chardet
import string


class FileUploader(ABC):
    """文件上传器抽象基类"""
    
    @abstractmethod
    def upload(self, data: Union[bytes, str, Path], filename: str = None) -> str:
        """
        上传文件
        Args:
            data: 文件数据，可以是 bytes、文件路径或 URL
            filename: 可选的文件名
        Returns:
            str: 结果URL
        """
        pass


class MinIOUploader(FileUploader):
    """MinIO/S3 上传器实现"""
    
    def __init__(self, endpoint_url: str, base_url: str, access_key: str, secret_key: str, bucket_name: str, region: str = 'us-east-1'):
        self.endpoint_url = endpoint_url
        self.base_url = base_url
        self.bucket_name = bucket_name
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name=region
        )
    
    def upload(self, data: Union[bytes, str, Path], filename: str = None) -> str:
        # 处理不同类型的输入
        file_content, file_name = self._process_input(data, filename)
        
        # 获取文件类型和编码，同时可能转换文件内容
        file_content, content_type = self._get_content_type(file_content, file_name)
        
        # 上传到 MinIO/S3
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=file_name,
            Body=file_content,
            ContentType=content_type
        )
        
        # 构造访问 URL
        url = f"{self.base_url.rstrip('/')}/{self.bucket_name}/{file_name}"
        return url
    
    def _process_input(self, data: Union[bytes, str, Path], filename: str = None) -> Tuple[Union[bytes, str], str]:
        """处理不同类型的输入数据"""
        # 生成UUID作为基础文件名
        base_name = uuid.uuid4().hex
        
        if isinstance(data, bytes):
            # 直接是字节数据
            # 从提供的filename获取扩展名，默认为.bin
            if filename:
                _, ext = os.path.splitext(filename)
            else:
                ext = ".bin"
            
            file_content = data
        
        elif isinstance(data, (str, Path)):
            data_str = str(data)
            
            # 判断是 URL 还是文件路径
            if data_str.startswith(('http://', 'https://')):
                # 是 URL，下载内容
                response = requests.get(data_str, timeout=30)
                response.raise_for_status()
                file_content = response.content
                
                # 确定文件扩展名
                if filename:
                    # 如果提供了filename，使用其扩展名
                    _, ext = os.path.splitext(filename)
                else:
                    # 从URL路径获取扩展名
                    parsed_url = urlparse(data_str)
                    url_filename = os.path.basename(parsed_url.path)
                    _, ext = os.path.splitext(url_filename)
            else:
                # 是文件路径
                file_path = Path(data_str)
                if not file_path.exists():
                    raise FileNotFoundError(f"文件不存在: {file_path}")
                
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # 确定文件扩展名
                if filename:
                    # 如果提供了filename，使用其扩展名
                    _, ext = os.path.splitext(filename)
                else:
                    # 使用原文件的扩展名
                    ext = file_path.suffix
        
        else:
            raise ValueError(f"不支持的数据类型: {type(data)}")
        
        # 统一拼接文件名
        file_name = f"{base_name}{ext}" if ext else base_name
        return file_content, file_name
    
    def _get_content_type(self, file_content: Union[bytes, str], file_name: str) -> Tuple[bytes, str]:
        """获取正确的Content-Type，特别处理文本文件的编码"""
        # 确保 file_content 是 bytes 类型
        if isinstance(file_content, str):
            file_content = file_content.encode('utf-8')
        
        # 先用 mimetypes 基于文件名猜测
        content_type, _ = mimetypes.guess_type(file_name)
        
        # 如果猜测不出来，通过内容判断是否为文本文件
        if content_type is None:
            if self._is_text_file(file_content):
                content_type = 'text/plain'
            else:
                content_type = 'application/octet-stream'
        
        # 如果是文本类型，需要检测编码并添加charset
        if content_type.startswith('text/'):
            # 检测文件编码
            try:
                detected = chardet.detect(file_content)
                encoding = detected.get('encoding') or 'utf-8'
                
                logger.info(f"检测到文件编码: {encoding}")
                
                # 添加charset信息
                content_type = f"{content_type}; charset={encoding}"
                
            except Exception as e:
                logger.warning(f"编码检测失败: {e}")
                content_type = f"{content_type}; charset=utf-8"
        
        return file_content, content_type
    
    def _is_text_file(self, file_content: bytes) -> bool:
        """判断文件内容是否为文本文件"""
        if len(file_content) == 0:
            return True
        
        # 取前1024字节进行检测
        sample = file_content[:1024]
        
        # 检查是否包含NULL字节（二进制文件的强指标）
        if b'\x00' in sample:
            return False
        
        # 尝试解码为文本
        try:
            # 先检测编码
            detected = chardet.detect(sample)
            encoding = detected.get('encoding')
            if encoding:
                text = sample.decode(encoding)
                # 检查是否主要由可打印字符组成
                printable_chars = sum(1 for c in text if c in string.printable)
                return printable_chars / len(text) > 0.7  # 70%以上为可打印字符
        except (UnicodeDecodeError, TypeError):
            pass
        
        return False


def upload(data: Union[bytes, str, Path], filename: str = None) -> str:
    """
    上传文件的统一接口
    Args:
        data: 文件数据，可以是 bytes、文件路径或 URL
        filename: 可选的文件名
    Returns:
        str: 结果URL
    """
    return default_uploader.upload(data, filename)


default_uploader = MinIOUploader(
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    base_url=os.getenv("MINIO_BASE_URL"),
    access_key=os.getenv("MINIO_USERNAME"),
    secret_key=os.getenv("MINIO_PASSWORD"),
    region=os.getenv("MINIO_REGION"),
    bucket_name=os.getenv("MINIO_BUCKET"),
)

# 使用示例和测试代码
if __name__ == "__main__":
    logger.info("\n1. 测试上传本地文件:")
    result = upload('temp/test.txt')
    logger.info(f'结果: {result}')
    