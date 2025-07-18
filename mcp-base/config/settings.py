"""
基础服务配置管理
支持多种存储后端的配置
"""

import os
from enum import Enum
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class StorageType(str, Enum):
    """存储类型枚举"""
    LOCAL = "local"
    MINIO = "minio"
    # 未来可扩展: OSS = "oss", COS = "cos"


class Settings(BaseSettings):
    """基础服务配置"""
    
    # 服务基础配置
    app_name: str = "Pixelle Base Service"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # 服务器配置
    base_server_host: str = "127.0.0.1"
    base_server_port: int = 9001
    public_read_url: Optional[str] = None  # 公开访问的URL，用于文件访问
    
    # 存储配置
    storage_type: StorageType = StorageType.LOCAL
    
    # 本地存储配置
    local_storage_path: str = "data/files"
    
    # MinIO配置（当storage_type=minio时使用）
    minio_endpoint: Optional[str] = "localhost:9000"
    minio_access_key: Optional[str] = "minio"
    minio_secret_key: Optional[str] = "minio1234"
    minio_bucket: Optional[str] = "files"
    minio_secure: bool = False
    
    # 文件配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: list[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",  # 图片
        ".mp4", ".avi", ".mov", ".mkv", ".webm",  # 视频
        ".mp3", ".wav", ".flac", ".aac", ".ogg",  # 音频
        ".txt", ".json", ".csv", ".pdf"  # 文档
    ]
    
    # API配置
    cors_origins: list[str] = ["*"]
    
    # 兼容性属性
    @property
    def host(self) -> str:
        """兼容性属性，返回base_server_host"""
        return self.base_server_host
    
    @property
    def port(self) -> int:
        """兼容性属性，返回base_server_port"""
        return self.base_server_port
    
    def get_base_url(self) -> str:
        """获取基础URL，优先使用PUBLIC_READ_URL，否则根据host:port构建"""
        if self.public_read_url:
            return self.public_read_url
        return f"http://{self.base_server_host}:{self.base_server_port}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# 全局配置实例
settings = Settings() 