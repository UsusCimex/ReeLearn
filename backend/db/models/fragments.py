from sqlalchemy import Column, Integer, String, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from db.base import Base

class Fragment(Base):
    __tablename__ = 'fragments'
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    timecode_start = Column(Integer, nullable=False)
    timecode_end = Column(Integer, nullable=False)
    s3_url = Column(String, nullable=False)
    text = Column(Text, nullable=True) 
    tags = Column(ARRAY(String), nullable=True)
    video = relationship('Video', back_populates='fragments')