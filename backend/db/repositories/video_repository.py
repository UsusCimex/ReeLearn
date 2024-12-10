from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.videos import Video
from ..models.fragments import Fragment
from utils.video_processing import VideoFragment
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

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

    async def update_video(self, video_id: int, **kwargs) -> Optional[Video]:
        video = await self.get_video_by_id(video_id)
        if video:
            for key, value in kwargs.items():
                setattr(video, key, value)
            await self.session.commit()
            await self.session.refresh(video)
        return video

    async def save_fragments(self, video_id: int, fragments: List[VideoFragment]) -> None:
        """Save video fragments to the database"""
        video = await self.get_video_by_id(video_id)
        if not video:
            return None
        
        # Create Fragment objects for each VideoFragment
        for fragment in fragments:
            # Skip fragments with empty s3_url
            if not fragment.s3_url:
                logger.warning(f"Skipping fragment with empty s3_url: {fragment.text[:50]}...")
                continue
                
            db_fragment = Fragment(
                video_id=video_id,
                timecode_start=fragment.start_time,
                timecode_end=fragment.end_time,
                s3_url=fragment.s3_url,
                text=fragment.text,
                tags=fragment.tags or [],
                speech_confidence=fragment.speech_confidence,
                no_speech_prob=fragment.no_speech_prob,
                language=fragment.language
            )
            self.session.add(db_fragment)
        
        await self.session.commit()
