import sys
import os

# Добавляем путь к backend в PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.fragments import Fragment
from db.models.videos import Video  # Добавляем импорт Video
from core.config import settings
from db.base import Base  # Добавляем импорт Base

# Создание engine и сессии
engine = create_engine(settings.SYNC_DATABASE_URL)
Base.metadata.create_all(bind=engine)  # Создаем таблицы если их нет
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

try:
    # Получаем все фрагменты
    fragments = session.query(Fragment).all()
    print(f"\nНайдено фрагментов в БД: {len(fragments)}")
    
    # Выводим информацию о каждом фрагменте
    for fragment in fragments[:5]:
        print(f"\nID: {fragment.id}")
        print(f"Text: {fragment.text}")
        print(f"Tags: {fragment.tags}")
        print(f"Video ID: {fragment.video_id}")
        print(f"Timecode: {fragment.timecode_start} - {fragment.timecode_end}")
finally:
    session.close()
