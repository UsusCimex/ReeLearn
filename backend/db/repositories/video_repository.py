from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.videos import Video
from typing import Optional

class VideoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_video(self, name: str, description: Optional[str], s3_url: str) -> Video:
        video = Video(name=name, description=description, s3_url=s3_url)
        self.session.add(video)
        await self.session.commit()
        await self.session.refresh(video)
        return video
    
    async def get_video_by_id(self, video_id: int) -> Optional[Video]:
        result = await self.session.execute(select(Video).where(Video.id == video_id))
        return result.scalars().first()
