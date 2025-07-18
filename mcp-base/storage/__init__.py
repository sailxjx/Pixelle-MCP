"""
存储模块
提供多种存储后端的统一接口
"""

from .base import StorageBackend, FileInfo
from .local_storage import LocalStorage
from .minio_storage import MinioStorage
from config.settings import settings, StorageType


class StorageFactory:
    """存储后端工厂类"""
    
    @staticmethod
    def create_storage() -> StorageBackend:
        """根据配置创建存储后端"""
        if settings.storage_type == StorageType.LOCAL:
            return LocalStorage()
        elif settings.storage_type == StorageType.MINIO:
            return MinioStorage()
        else:
            raise ValueError(f"Unsupported storage type: {settings.storage_type}")


# 全局存储实例
storage = StorageFactory.create_storage()


__all__ = [
    "StorageBackend", 
    "FileInfo", 
    "LocalStorage", 
    "MinioStorage", 
    "StorageFactory", 
    "storage"
] 