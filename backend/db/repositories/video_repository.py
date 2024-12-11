from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models.videos import Video
from ..models.fragments import Fragment
from ..models.video_fragment import VideoFragment
from utils.elasticsearch_utils import add_new_fragment
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class VideoRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create_video(
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
        self.session.flush()
        self.session.refresh(video)
        return video
    
    def get_video_by_id(self, video_id: int) -> Optional[Video]:
        result = self.session.execute(select(Video).where(Video.id == video_id))
        return result.scalars().first()
    
    def update_video_status(self, video_id: int, status: str) -> Optional[Video]:
        video = self.get_video_by_id(video_id)
        if video:
            video.status = status
            self.session.flush()
        return video

    def update_video(self, video_id: int, **kwargs) -> Optional[Video]:
        video = self.get_video_by_id(video_id)
        if video:
            for key, value in kwargs.items():
                setattr(video, key, value)
            self.session.flush()
        return video

    def save_fragments(self, video_id: int, fragments: List[VideoFragment]) -> None:
        """Save video fragments to the database and index them in Elasticsearch"""
        video = self.get_video_by_id(video_id)
        if not video:
            logger.error(f"Video with id {video_id} not found")
            return None
        
        saved_fragments = []
        for fragment in fragments:
            db_fragment = Fragment(
                video_id=video_id,
                timecode_start=fragment.start_time,
                timecode_end=fragment.end_time,
                s3_url=fragment.s3_url,
                text=fragment.text,
                tags=fragment.tags,
                speech_confidence=fragment.speech_confidence,
                no_speech_prob=fragment.no_speech_prob,
                language=fragment.language
            )
            self.session.add(db_fragment)
            saved_fragments.append(db_fragment)
        
        if not saved_fragments:
            logger.warning(f"No valid fragments to save for video {video_id}")
            return None

        try:
            # Save to database and get IDs
            self.session.flush()
            
            # Index in Elasticsearch
            indexed_count = 0
            for fragment in saved_fragments:
                try:
                    add_new_fragment(fragment)
                    indexed_count += 1
                    logger.debug(f"Fragment {fragment.id} indexed in Elasticsearch")
                except Exception as e:
                    logger.error(f"Failed to index fragment in Elasticsearch: {str(e)}")
            
            logger.info(f"Successfully indexed {indexed_count}/{len(saved_fragments)} fragments in Elasticsearch for video {video_id}")
            
        except Exception as e:
            logger.error(f"Error saving fragments for video {video_id}: {str(e)}")
            raise e

    def get_all_videos_with_fragments_count(self) -> List[dict]:
        """Получить все видео с количеством фрагментов."""
        videos = self.session.execute(select(Video)).scalars().all()
        result = []
        
        for video in videos:
            fragments_count = self.session.execute(
                select(func.count(Fragment.id))
                .where(Fragment.video_id == video.id)
            ).scalar()
            
            result.append({
                "id": video.id,
                "name": video.name,
                "status": video.status,
                "fragments_count": fragments_count or 0
            })
        
        return result

    def get_video_fragments(self, video_id: int) -> List[Fragment]:
        """Получить все фрагменты видео, отсортированные по времени начала."""
        return self.session.execute(
            select(Fragment)
            .where(Fragment.video_id == video_id)
            .order_by(Fragment.timecode_start)
        ).scalars().all()

    def get_fragment_by_id(self, fragment_id: int) -> Optional[Fragment]:
        """Get a video fragment by its ID."""
        return self.session.query(Fragment).filter(Fragment.id == fragment_id).first()
