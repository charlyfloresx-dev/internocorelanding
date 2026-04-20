import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.core.config import settings


def get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.MINIO_URL,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket_exists():
    """Creates the kiosk bucket if it doesn't exist."""
    client = get_minio_client()
    try:
        client.head_bucket(Bucket=settings.MINIO_BUCKET_NAME)
    except ClientError:
        client.create_bucket(Bucket=settings.MINIO_BUCKET_NAME)


def generate_presigned_upload_url(object_key: str, content_type: str, expires: int = 300) -> str:
    """
    Generates a Presigned PUT URL so the client can upload directly to MinIO.
    The server never handles the raw bytes — max speed.
    """
    client = get_minio_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.MINIO_BUCKET_NAME,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires,
    )
    return url


def generate_presigned_download_url(object_key: str, expires: int = 3600) -> str:
    """Generates a temporary GET URL to display the photo in the frontend.
    
    The URL is generated using the internal MINIO_URL but rewritten to
    MINIO_PUBLIC_URL so browsers outside Docker can resolve it.
    """
    client = get_minio_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.MINIO_BUCKET_NAME, "Key": object_key},
        ExpiresIn=expires,
    )
    # Force replace any mention of the internal 'minio' hostname or the MINIO_URL 
    # with the PUBLIC_URL so the browser can actually fetch the images.
    public_url = settings.MINIO_PUBLIC_URL.rstrip("/")
    internal_url = settings.MINIO_URL.rstrip("/")
    
    url = url.replace(internal_url, public_url)
    url = url.replace("http://minio:9000", public_url) # Safety fallback
    
    return url



def get_object_stream(object_key: str):
    """Fetches the actual bytes of the object from MinIO."""
    client = get_minio_client()
    response = client.get_object(Bucket=settings.MINIO_BUCKET_NAME, Key=object_key)
    return response["Body"], response["ContentType"]


def delete_object(object_key: str):
    client = get_minio_client()
    client.delete_object(Bucket=settings.MINIO_BUCKET_NAME, Key=object_key)
