from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
import os
import boto3
from botocore.exceptions import ClientError
from common.config import settings

class StorageProvider(ABC):
    @abstractmethod
    def upload_file(self, file_obj: BinaryIO, object_key: str, content_type: Optional[str] = None) -> str:
        """
        Uploads a file and returns the URI (S3 Key or Local Path).
        """
        pass

    @abstractmethod
    def delete_file(self, object_key: str) -> bool:
        """
        Deletes a file from storage.
        """
        pass

    @abstractmethod
    def get_url(self, object_key: str, expires_in: int = 3600) -> str:
        """
        Returns a URL to access the file (Public | Presigned).
        """
        pass


class S3StorageProvider(StorageProvider):
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET
        # Usamos endpoint_url si está en config (LocalStack/MinIO) o None para AWS real
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.int_aws_region
        )

    def upload_file(self, file_obj: BinaryIO, object_key: str, content_type: Optional[str] = None) -> str:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        # Reset file pointer just in case
        file_obj.seek(0)
        self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_key, ExtraArgs=extra_args)
        return object_key

    def delete_file(self, object_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    def get_url(self, object_key: str, expires_in: int = 3600) -> str:
        # Si tenemos un CDN (CloudFront) configurado, retornamos la URL directa
        if settings.S3_PUBLIC_URL:
            clean_host = settings.S3_PUBLIC_URL.rstrip('/')
            return f"{clean_host}/{object_key}"
        
        # De lo contrario generamos una URL pre-firmada (segura)
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError:
            return ""


class LocalStorageProvider(StorageProvider):
    def __init__(self):
        self.base_path = settings.LOCAL_STORAGE_PATH
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

    def upload_file(self, file_obj: BinaryIO, object_key: str, content_type: Optional[str] = None) -> str:
        file_path = os.path.join(self.base_path, object_key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_obj.seek(0)
        with open(file_path, "wb") as f:
            f.write(file_obj.read())
        return object_key

    def delete_file(self, object_key: str) -> bool:
        file_path = os.path.join(self.base_path, object_key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def get_url(self, object_key: str, expires_in: int = 3600) -> str:
        # En local devolvemos una ruta relativa o un endpoint de proxy si existiera
        return f"/api/v1/storage/{object_key}"


def get_storage_provider() -> StorageProvider:
    if settings.STORAGE_BACKEND.upper() == "S3":
        return S3StorageProvider()
    return LocalStorageProvider()
