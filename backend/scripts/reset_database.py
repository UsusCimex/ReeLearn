import sys
import os

# Add backend path to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from db.base import Base
from core.config import settings
from db.models.fragments import Fragment
from db.models.videos import Video

def reset_database():
    print("Creating database engine...")
    engine = create_engine(settings.SYNC_DATABASE_URL)
    
    print("\nDropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("\nCreating all tables with new schema...")
    Base.metadata.create_all(bind=engine)
    
    print("\nDatabase reset complete!")

if __name__ == "__main__":
    reset_database()
