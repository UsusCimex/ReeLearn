import asyncio
import aioboto3
import aiofiles
import os
import logging
import json
from urllib.parse import urlparse
from core.config import settings
from botocore.exceptions import ClientError
from contextlib import asynccontextmanager
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_s3_session = None

def get_s3_session():
    global _s3_session
    if _s3_session is None:
        _s3_session = aioboto3.Session()
    return _s3_session

@asynccontextmanager
async def get_s3_client():
    session = get_s3_session()
    async with session.client(
        's3',
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY
    ) as client:
        try:
            yield client
        finally:
            await client.close()

async def upload_file_to_s3(file_path: str, key: str) -> str:
    """Upload a file to S3 and return its public URL."""
    logger.info(f"Starting S3 upload for file: {file_path}")
    
    # Ensure bucket exists with proper configuration
    await ensure_bucket_exists()
    
    async with get_s3_client() as s3_client:
        try:
            # Используем multipart upload для больших файлов
            async with aiofiles.open(file_path, 'rb') as f:
                file_size = os.path.getsize(file_path)
                logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
                
                if file_size > 5 * 1024 * 1024:  # Если файл больше 5MB
                    logger.info("Using multipart upload")
                    # Инициализируем multipart upload
                    mpu = await s3_client.create_multipart_upload(
                        Bucket=settings.S3_BUCKET_NAME,
                        Key=key
                    )
                    logger.info(f"Multipart upload initiated with ID: {mpu['UploadId']}")
                    
                    parts = []
                    part_number = 1
                    chunk_size = 5 * 1024 * 1024  # 5MB chunks
                    total_uploaded = 0
                    
                    while True:
                        chunk = await f.read(chunk_size)
                        if not chunk:
                            break
                            
                        # Загружаем часть
                        logger.info(f"Uploading part {part_number}")
                        part = await s3_client.upload_part(
                            Bucket=settings.S3_BUCKET_NAME,
                            Key=key,
                            PartNumber=part_number,
                            UploadId=mpu['UploadId'],
                            Body=chunk
                        )
                        
                        total_uploaded += len(chunk)
                        logger.info(f"Uploaded {total_uploaded / (1024*1024):.2f} MB ({(total_uploaded/file_size)*100:.1f}%)")
                        
                        parts.append({
                            'PartNumber': part_number,
                            'ETag': part['ETag']
                        })
                        part_number += 1
                    
                    # Завершаем multipart upload
                    logger.info("Completing multipart upload")
                    await s3_client.complete_multipart_upload(
                        Bucket=settings.S3_BUCKET_NAME,
                        Key=key,
                        UploadId=mpu['UploadId'],
                        MultipartUpload={'Parts': parts}
                    )
                else:
                    logger.info("Using single-part upload")
                    await s3_client.upload_fileobj(f, settings.S3_BUCKET_NAME, key)
                    
            s3_url = f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET_NAME}/{key}"
            logger.info(f"Upload complete, URL: {s3_url}")
            return s3_url
        except ClientError as ce:
            logger.error(f"S3 ClientError: {ce}")
            raise HTTPException(status_code=500, detail=f"S3 ClientError: {ce}")
        except Exception as e:
            logger.error(f"General Exception during S3 upload: {e}")
            raise HTTPException(status_code=500, detail=f"General Exception: {e}")

async def download_file_from_s3(s3_url: str, destination_path: str) -> bool:
    try:
        parsed_url = urlparse(s3_url)
        path_parts = parsed_url.path.lstrip('/').split('/', 1)
        if len(path_parts) != 2:
            raise ValueError("Неверный формат S3 URL")
        bucket_name, key = path_parts

        async with get_s3_client() as s3_client:
            async with aiofiles.open(destination_path, 'wb') as f:
                response = await s3_client.get_object(Bucket=bucket_name, Key=key)
                async for chunk in response['Body'].iter_chunks():
                    await f.write(chunk)
            return True
    except Exception as e:
        print(f"Ошибка при скачивании файла из S3: {e}")
        return False

async def ensure_bucket_exists():
    """Ensure the bucket exists and has proper public access configuration."""
    async with get_s3_client() as s3_client:
        try:
            # Create bucket if it doesn't exist
            try:
                await s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            except ClientError:
                await s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                logger.info(f"Created bucket: {settings.S3_BUCKET_NAME}")

            # Set bucket policy to allow public read access
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicRead",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{settings.S3_BUCKET_NAME}/*"]
                    }
                ]
            }
            
            await s3_client.put_bucket_policy(
                Bucket=settings.S3_BUCKET_NAME,
                Policy=json.dumps(policy)
            )
            logger.info(f"Set public read policy for bucket: {settings.S3_BUCKET_NAME}")

        except Exception as e:
            logger.error(f"Error configuring bucket: {e}")
            raise

async def generate_presigned_url(s3_url: str, expiration=3600):
    """
    Генерирует presigned URL для доступа к объекту в S3.
    
    :param s3_url: URL объекта в S3
    :param expiration: Время жизни URL в секундах
    :return: Публичный presigned URL
    """
    parsed_url = urlparse(s3_url)
    path_parts = parsed_url.path.lstrip('/').split('/', 1)
    if len(path_parts) != 2:
        raise ValueError("Неверный формат S3 URL")
    bucket_name, key = path_parts

    async with get_s3_client() as s3_client:
        try:
            # Генерируем presigned URL с использованием внутреннего эндпоинта
            presigned_url = await s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            
            # Заменяем внутренний эндпоинт на публичный в сгенерированном URL
            if settings.S3_ENDPOINT_URL and settings.S3_PUBLIC_URL:
                presigned_url = presigned_url.replace(
                    settings.S3_ENDPOINT_URL,
                    settings.S3_PUBLIC_URL
                )
            
            return presigned_url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
