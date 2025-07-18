"""
MinIO文件存储实现
将文件存储到MinIO对象存储
"""

import uuid
import mimetypes
from io import BytesIO
from typing import BinaryIO, Optional
from minio import Minio
from minio.error import S3Error

from .base import StorageBackend, FileInfo
from config.settings import settings


class MinioStorage(StorageBackend):
    """MinIO文件存储"""
    
    def __init__(
        self, 
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket: Optional[str] = None,
        secure: Optional[bool] = None
    ):
        self.endpoint = endpoint or settings.minio_endpoint
        self.access_key = access_key or settings.minio_access_key
        self.secret_key = secret_key or settings.minio_secret_key
        self.bucket = bucket or settings.minio_bucket
        self.secure = secure if secure is not None else settings.minio_secure
        
        # 初始化MinIO客户端
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # 确保bucket存在
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    def _generate_file_id(self, filename: str) -> str:
        """生成唯一的文件ID"""
        # 保留文件扩展名
        from pathlib import Path
        ext = Path(filename).suffix
        return f"{uuid.uuid4().hex}{ext}"
    
    def _get_file_url(self, file_id: str) -> str:
        """获取文件的访问URL"""
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}/{self.bucket}/{file_id}"
    
    async def upload(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        content_type: str
    ) -> FileInfo:
        """上传文件到MinIO"""
        # 生成唯一文件ID
        file_id = self._generate_file_id(filename)
        
        # 读取文件内容
        content = file_data.read()
        file_size = len(content)
        
        try:
            # 上传到MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=file_id,
                data=BytesIO(content),
                length=file_size,
                content_type=content_type
            )
            
            return FileInfo(
                file_id=file_id,
                filename=filename,
                content_type=content_type,
                size=file_size,
                url=self._get_file_url(file_id)
            )
        except S3Error as e:
            raise Exception(f"Failed to upload file to MinIO: {e}")
    
    async def download(self, file_id: str) -> Optional[bytes]:
        """从MinIO下载文件"""
        try:
            response = self.client.get_object(self.bucket, file_id)
            content = response.read()
            response.close()
            response.release_conn()
            return content
        except S3Error:
            return None
    
    async def delete(self, file_id: str) -> bool:
        """从MinIO删除文件"""
        try:
            self.client.remove_object(self.bucket, file_id)
            return True
        except S3Error:
            return False
    
    async def exists(self, file_id: str) -> bool:
        """检查MinIO中文件是否存在"""
        try:
            self.client.stat_object(self.bucket, file_id)
            return True
        except S3Error:
            return False
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """获取MinIO中文件信息"""
        try:
            stat = self.client.stat_object(self.bucket, file_id)
            
            return FileInfo(
                file_id=file_id,
                filename=file_id,  # MinIO中使用file_id作为文件名
                content_type=stat.content_type or "application/octet-stream",
                size=stat.size,
                url=self._get_file_url(file_id)
            )
        except S3Error:
            return None 