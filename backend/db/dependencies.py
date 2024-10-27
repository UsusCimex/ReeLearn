from db.base import async_session
from sqlalchemy.ext.asyncio import AsyncSession

# Зависимость для получения сессии базы данных
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
