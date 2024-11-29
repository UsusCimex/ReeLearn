from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.videos import Video
from typing import Optional

class VideoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_video(
        self, 
        name: str, 
        description: Optional[str], 
        s3_url: str,
        status: str = 'pending'
    ) -> Video:
        video = Video(
            name=name, 
            description=description, 
            s3_url=s3_url,
            status=status
        )
        self.session.add(video)
        await self.session.commit()
        await self.session.refresh(video)
        return video
    
    async def get_video_by_id(self, video_id: int) -> Optional[Video]:
        result = await self.session.execute(select(Video).where(Video.id == video_id))
        return result.scalars().first()
    
    async def update_video_status(self, video_id: int, status: str) -> Optional[Video]:
        video = await self.get_video_by_id(video_id)
        if video:
            video.status = status
            await self.session.commit()
            await self.session.refresh(video)
        return video
