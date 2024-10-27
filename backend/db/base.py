from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Создание асинхронного движка
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Создание асинхронной фабрики сессий
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()
