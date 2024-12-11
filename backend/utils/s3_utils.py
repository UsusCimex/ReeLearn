import boto3
import os
import logging
import json
from urllib.parse import urlparse
from core.config import settings
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def get_s3_client():
    """Создает клиент S3."""
    return boto3.client(
        's3',
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY
    )

def upload_file_to_s3(file_path: str, key: str = None) -> str:
    """
    Загружает файл в S3 и возвращает его ключ.
    
    Args:
        file_path: Путь к загружаемому файлу
        key: Ключ объекта в S3 (если не указан, используется имя файла)
        
    Returns:
        str: Ключ объекта в S3
    """
    if key is None:
        key = os.path.basename(file_path)
        
    logger.info(f"Starting S3 upload for file: {file_path}")
    
    ensure_bucket_exists()
    s3_client = get_s3_client()
    
    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
        
        if file_size > 5 * 1024 * 1024:  # Если файл > 5MB
            mpu = s3_client.create_multipart_upload(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key
            )
            
            parts = []
            chunk_size = 5 * 1024 * 1024  # 5MB chunks
            
            with open(file_path, 'rb') as f:
                part_number = 1
                
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    part = s3_client.upload_part(
                        Bucket=settings.S3_BUCKET_NAME,
                        Key=key,
                        PartNumber=part_number,
                        UploadId=mpu['UploadId'],
                        Body=chunk
                    )
                    
                    parts.append({
                        'PartNumber': part_number,
                        'ETag': part['ETag']
                    })
                    part_number += 1
            
            s3_client.complete_multipart_upload(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key,
                UploadId=mpu['UploadId'],
                MultipartUpload={'Parts': parts}
            )
        else:
            with open(file_path, 'rb') as f:
                s3_client.upload_fileobj(f, settings.S3_BUCKET_NAME, key)
        
        logger.info(f"Successfully uploaded file to S3: {key}")
        return key
        
    except Exception as e:
        logger.error(f"Error uploading file to S3: {str(e)}")
        raise Exception(f"Failed to upload file to S3: {str(e)}")

def download_file_from_s3(s3_url: str, destination_path: str) -> bool:
    """Скачивает файл из S3."""
    try:
        parsed = urlparse(s3_url)
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        
        s3_client = get_s3_client()
        s3_client.download_file(bucket, key, destination_path)
        return True
    except Exception as e:
        logger.error(f"Error downloading file from S3: {str(e)}")
        return False

def ensure_bucket_exists():
    """Проверяет существование бакета и создает его при необходимости."""
    s3_client = get_s3_client()
    
    try:
        s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        logger.info(f"Bucket {settings.S3_BUCKET_NAME} exists")
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            logger.info(f"Creating bucket {settings.S3_BUCKET_NAME}")
            try:
                # Создаем бакет без указания региона (для MinIO это не требуется)
                s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                
                try:
                    # Пытаемся настроить CORS, но пропускаем если не поддерживается
                    cors_configuration = {
                        'CORSRules': [{
                            'AllowedHeaders': ['*'],
                            'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                            'AllowedOrigins': settings.ALLOWED_ORIGINS,
                            'ExposeHeaders': ['ETag']
                        }]
                    }
                    s3_client.put_bucket_cors(
                        Bucket=settings.S3_BUCKET_NAME,
                        CORSConfiguration=cors_configuration
                    )
                    logger.info("CORS configuration applied successfully")
                except ClientError as cors_error:
                    if 'NotImplemented' in str(cors_error):
                        logger.warning("CORS configuration not supported by this S3 implementation - skipping")
                    else:
                        logger.warning(f"Failed to set CORS configuration: {str(cors_error)}")
                
                try:
                    # Настройка публичного доступа к бакету
                    bucket_policy = {
                        'Version': '2012-10-17',
                        'Statement': [{
                            'Sid': 'PublicReadGetObject',
                            'Effect': 'Allow',
                            'Principal': '*',
                            'Action': ['s3:GetObject'],
                            'Resource': [f'arn:aws:s3:::{settings.S3_BUCKET_NAME}/*']
                        }]
                    }
                    s3_client.put_bucket_policy(
                        Bucket=settings.S3_BUCKET_NAME,
                        Policy=json.dumps(bucket_policy)
                    )
                    logger.info("Bucket policy applied successfully")
                except ClientError as policy_error:
                    logger.warning(f"Failed to set bucket policy: {str(policy_error)}")
                
                logger.info(f"Successfully created bucket {settings.S3_BUCKET_NAME}")
            except Exception as create_error:
                logger.error(f"Failed to create bucket: {str(create_error)}")
                raise
        else:
            logger.error(f"Error checking bucket: {str(e)}")
            raise

def generate_presigned_url(s3_key: str, expiration: int = 3600) -> str:
    """
    Генерирует предподписанный URL для доступа к объекту в S3.
    
    Args:
        s3_key: Ключ объекта в S3 или полный URL в формате s3://bucket/key
        expiration: Время жизни URL в секундах (по умолчанию 1 час)
    
    Returns:
        str: Предподписанный URL с публичным доступом
    """
    try:
        # Extract key if it's a full S3 URL
        if s3_key.startswith('s3://'):
            parsed = urlparse(s3_key)
            key = parsed.path.lstrip('/')
        else:
            key = s3_key.lstrip('/')
        
        # Generate presigned URL
        s3_client = get_s3_client()
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': key
            },
            ExpiresIn=expiration
        )
        
        # Replace internal minio URL with public URL
        if settings.S3_ENDPOINT_URL != settings.S3_PUBLIC_URL:
            url = url.replace(settings.S3_ENDPOINT_URL, settings.S3_PUBLIC_URL)
            
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise
