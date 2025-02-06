import boto3
import os
import logging
import json
from urllib.parse import urlparse
from core.config import settings
from botocore.exceptions import ClientError

logger = logging.getLogger("ReeLearnLogger")

def get_s3_client():
    return boto3.client("s3", endpoint_url=settings.S3_ENDPOINT_URL, aws_access_key_id=settings.S3_ACCESS_KEY, aws_secret_access_key=settings.S3_SECRET_KEY)

def ensure_bucket_exists():
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except ClientError:
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)

def upload_file_to_s3(file_path: str, key: str = None) -> str:
    if not key:
        key = os.path.basename(file_path)
    ensure_bucket_exists()
    s3 = get_s3_client()
    size = os.path.getsize(file_path)
    if size > 5 * 1024 * 1024:
        mpu = s3.create_multipart_upload(Bucket=settings.S3_BUCKET_NAME, Key=key)
        parts = []
        chunk_size = 5 * 1024 * 1024
        with open(file_path, "rb") as f:
            part_number = 1
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                part = s3.upload_part(Bucket=settings.S3_BUCKET_NAME, Key=key, PartNumber=part_number, UploadId=mpu["UploadId"], Body=chunk)
                parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
                part_number += 1
        s3.complete_multipart_upload(Bucket=settings.S3_BUCKET_NAME, Key=key, UploadId=mpu["UploadId"], MultipartUpload={"Parts": parts})
    else:
        with open(file_path, "rb") as f:
            s3.upload_fileobj(f, settings.S3_BUCKET_NAME, key)
    return key

def download_file_from_s3(s3_url: str, destination_path: str) -> bool:
    parsed = urlparse(s3_url)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    s3 = get_s3_client()
    s3.download_file(bucket, key, destination_path)
    return True

def generate_presigned_url(s3_key: str, expiration: int = 3600) -> str:
    if not s3_key or len(s3_key.strip()) == 0:
        logger.warning("generate_presigned_url вызвана с пустым ключом.")
        return ""
    try:
        if s3_key.startswith("s3://"):
            parsed = urlparse(s3_key)
            key = parsed.path.lstrip("/")
        else:
            key = s3_key.lstrip("/")
        s3_client = get_s3_client()
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': key
            },
            ExpiresIn=expiration
        )
        logger.info(f"Сгенерирован предоподписанный URL для ключа {key}: {url}")
        if settings.S3_ENDPOINT_URL != settings.S3_PUBLIC_URL:
            url = url.replace(settings.S3_ENDPOINT_URL, settings.S3_PUBLIC_URL)
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL for key '{s3_key}': {str(e)}", exc_info=True)
        return ""

def delete_file_from_s3(s3_url: str):
    parsed = urlparse(s3_url)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    s3 = get_s3_client()
    s3.delete_object(Bucket=bucket, Key=key)
