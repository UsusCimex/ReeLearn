import boto3
from urllib.parse import urlparse
from core.config import settings
from botocore.exceptions import ClientError

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION  # Добавьте, если необходимо
    )

def upload_file_to_s3(file_path: str, key: str) -> str:
    """
    Загружает файл в S3 и возвращает его URL.
    
    :param file_path: Путь к локальному файлу.
    :param key: Ключ (имя файла) в S3.
    :return: URL файла в S3.
    """
    s3_client = get_s3_client()
    try:
        s3_client.upload_file(file_path, settings.S3_BUCKET_NAME, key)
        s3_url = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{key}"
        return s3_url
    except ClientError as e:
        print(f"Ошибка при загрузке файла в S3: {e}")
        raise e

def download_file_from_s3(s3_url: str, destination_path: str) -> bool:
    """
    Скачивает файл из S3 в локальное место.
    
    :param s3_url: Полный URL файла в S3.
    :param destination_path: Путь для сохранения скачанного файла.
    :return: True, если успешно, иначе False.
    """
    try:
        parsed_url = urlparse(s3_url)
        path_parts = parsed_url.path.lstrip('/').split('/', 1)
        if len(path_parts) != 2:
            raise ValueError("Неверный формат S3 URL")
        bucket_name, key = path_parts
        s3_client = get_s3_client()
        s3_client.download_file(bucket_name, key, destination_path)
        return True
    except ClientError as e:
        print(f"Ошибка при скачивании файла из S3: {e}")
        return False
    except ValueError as e:
        print(f"Ошибка при разборе S3 URL: {e}")
        return False

def generate_presigned_url(s3_url: str, expiration=3600):
    """
    Генерирует presigned URL для скачивания файла из S3.
    
    :param s3_url: Полный URL файла в S3.
    :param expiration: Время жизни ссылки в секундах.
    :return: presigned URL.
    """
    try:
        parsed_url = urlparse(s3_url)
        path_parts = parsed_url.path.lstrip('/').split('/', 1)
        if len(path_parts) != 2:
            raise ValueError("Неверный формат S3 URL")
        bucket_name, key = path_parts
        s3_client = get_s3_client()
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=expiration
        )
        return presigned_url
    except ClientError as e:
        print(f"Ошибка при генерации presigned URL: {e}")
        raise e
    except ValueError as e:
        print(f"Ошибка при разборе S3 URL: {e}")
        raise e
