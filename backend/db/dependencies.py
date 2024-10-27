from db.base import async_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

# Зависимость для получения сессии базы данных
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
