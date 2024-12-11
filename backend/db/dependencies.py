from db.base import Session
from sqlalchemy.orm import Session
from contextlib import contextmanager

# Зависимость для получения сессии базы данных
@contextmanager
def get_db() -> Session:
    """Зависимость для получения сессии базы данных"""
    session = Session()
    try:
        yield session
    finally:
        session.close()
