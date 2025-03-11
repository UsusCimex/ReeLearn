import boto3
import os
import logging
import json
from urllib.parse import urlparse
from core.config import settings
from botocore.exceptions import ClientError
import time
import math

logger = logging.getLogger("ReeLearnLogger")

def get_s3_client():
    return boto3.client("s3", 
                       endpoint_url=settings.S3_ENDPOINT_URL, 
                       aws_access_key_id=settings.S3_ACCESS_KEY, 
                       aws_secret_access_key=settings.S3_SECRET_KEY,
                       config=boto3.session.Config(
                           connect_timeout=300,  # 5 минут для соединения
                           read_timeout=300,     # 5 минут для чтения
                           retries={'max_attempts': 5}  # 5 повторов при ошибках
                       ))

def ensure_bucket_exists():
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        logger.info(f"Бакет {settings.S3_BUCKET_NAME} уже существует")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            logger.info(f"Создание бакета {settings.S3_BUCKET_NAME}")
            s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        else:
            logger.error(f"Ошибка при проверке бакета: {str(e)}")
            raise

def calculate_part_size(file_size):
    """
    Рассчитывает оптимальный размер части для многопоточной загрузки.
    Для S3 API минимальный размер части должен быть 5MB, а максимальное количество частей - 10000.
    """
    min_part_size = 5 * 1024 * 1024  # 5 MB
    max_parts = 10000
    
    # Рассчитываем минимальный размер части, чтобы не превысить максимальное количество частей
    optimal_part_size = max(min_part_size, math.ceil(file_size / max_parts))
    
    # Округляем до ближайшего целого МБ
    optimal_part_size = math.ceil(optimal_part_size / (1024 * 1024)) * 1024 * 1024
    
    return optimal_part_size

def upload_file_to_s3(file_path: str, key: str = None, use_multipart: bool = True) -> str:
    """
    Загружает файл в S3 с оптимизацией для больших файлов.
    Аргументы:
        file_path: путь к локальному файлу
        key: ключ, под которым файл будет сохранен в S3
        use_multipart: использовать многопоточную загрузку
    Возвращает:
        ключ загруженного файла
    """
    if not key:
        key = os.path.basename(file_path)
        
    ensure_bucket_exists()
    s3 = get_s3_client()
    file_size = os.path.getsize(file_path)
    
    # Логируем информацию о загрузке
    logger.info(f"Начало загрузки файла {file_path} (размер: {file_size/1024/1024:.2f} МБ) с ключом {key} в S3")
    start_time = time.time()
    
    try:
        if use_multipart and file_size > 5 * 1024 * 1024:  # Используем многопоточную загрузку для файлов > 5 МБ
            # Рассчитываем оптимальный размер части
            part_size = calculate_part_size(file_size)
            
            logger.info(f"Используется многопоточная загрузка с размером части {part_size/1024/1024:.2f} МБ")
            
            # Инициализация многопоточной загрузки
            mpu = s3.create_multipart_upload(Bucket=settings.S3_BUCKET_NAME, Key=key)
            upload_id = mpu["UploadId"]
            
            parts = []
            chunk_count = math.ceil(file_size / part_size)
            
            with open(file_path, "rb") as f:
                for part_number in range(1, chunk_count + 1):
                    offset = (part_number - 1) * part_size
                    f.seek(offset)
                    chunk = f.read(part_size)
                    
                    if not chunk:  # Конец файла
                        break
                        
                    # Логируем прогресс каждые 10 частей
                    if part_number % 10 == 0 or part_number == 1 or part_number == chunk_count:
                        logger.info(f"Загрузка части {part_number}/{chunk_count} размером {len(chunk)/1024/1024:.2f} МБ")
                        
                    # Повторные попытки загрузки части при сбоях
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            part = s3.upload_part(
                                Bucket=settings.S3_BUCKET_NAME,
                                Key=key,
                                PartNumber=part_number,
                                UploadId=upload_id,
                                Body=chunk
                            )
                            parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
                            break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                logger.warning(f"Ошибка при загрузке части {part_number}, повтор {attempt + 1}: {str(e)}")
                                time.sleep(1)  # Пауза перед повторной попыткой
                            else:
                                logger.error(f"Ошибка при загрузке части {part_number} после {max_retries} попыток: {str(e)}")
                                # Отменяем многопоточную загрузку при ошибке
                                s3.abort_multipart_upload(
                                    Bucket=settings.S3_BUCKET_NAME,
                                    Key=key,
                                    UploadId=upload_id
                                )
                                raise
            
            # Завершаем многопоточную загрузку
            s3.complete_multipart_upload(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts}
            )
        else:
            # Для небольших файлов используем обычную загрузку
            logger.info(f"Используется обычная загрузка для файла размером {file_size/1024/1024:.2f} МБ")
            with open(file_path, "rb") as f:
                s3.upload_fileobj(f, settings.S3_BUCKET_NAME, key)
        
        end_time = time.time()
        duration = end_time - start_time
        transfer_rate = file_size / (1024 * 1024) / duration if duration > 0 else 0
        logger.info(f"Загрузка файла {key} завершена за {duration:.2f} секунд. Скорость: {transfer_rate:.2f} МБ/с")
        
        return key
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {file_path} в S3: {str(e)}", exc_info=True)
        raise

def download_file_from_s3(s3_url: str, destination_path: str) -> bool:
    """
    Скачивает файл из S3 с повторными попытками при сбоях.
    """
    parsed = urlparse(s3_url)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    
    if not bucket:
        bucket = settings.S3_BUCKET_NAME
    
    s3 = get_s3_client()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            s3.download_file(bucket, key, destination_path)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Ошибка при скачивании файла {key}, повтор {attempt + 1}: {str(e)}")
                time.sleep(2)  # Пауза перед повторной попыткой
            else:
                logger.error(f"Ошибка при скачивании файла {key} после {max_retries} попыток: {str(e)}")
                raise

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

def delete_file_from_s3(s3_url: str) -> bool:
    """
    Удаляет файл из S3.
    Возвращает True при успешном удалении.
    """
    try:
        if not s3_url or len(s3_url.strip()) == 0:
            logger.warning("delete_file_from_s3 вызвана с пустым ключом.")
            return False
            
        parsed = urlparse(s3_url)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        
        if not bucket:
            bucket = settings.S3_BUCKET_NAME
            key = s3_url
            
        s3 = get_s3_client()
        s3.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Файл {key} успешно удален из бакета {bucket}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении файла {s3_url} из S3: {str(e)}")
        return False
