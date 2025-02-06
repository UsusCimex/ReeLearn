from sqlalchemy import Column, Integer, String, Text, Enum
from sqlalchemy.orm import relationship
from db.base import Base
from schemas.upload import UploadStatus

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    s3_url = Column(String, nullable=True)
    status = Column(Enum(UploadStatus), nullable=False, default=UploadStatus.uploading)
    fragments = relationship("Fragment", back_populates="video", cascade="all, delete-orphan")
