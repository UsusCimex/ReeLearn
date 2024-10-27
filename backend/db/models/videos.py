from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.base import Base

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    fragments = relationship('Fragment', back_populates='video')
