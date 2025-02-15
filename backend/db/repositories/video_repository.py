from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete
from db.models.video import Video
from db.models.fragment import Fragment
from db.models.video_fragment import VideoFragment as VideoFragmentData
from utils.elasticsearch_utils import add_new_fragment
import logging

logger = logging.getLogger("ReeLearnLogger")

class VideoRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_video(self, name: str, description: str, s3_url: str, status: str):
        video = Video(name=name, description=description, s3_url=s3_url, status=status)
        self.db.add(video)
        self.db.flush()
        self.db.refresh(video)
        return video
    
    def get_video_by_id(self, video_id: int):
        return self.db.execute(select(Video).where(Video.id == video_id)).scalars().first()
    
    def update_video_status(self, video_id: int, status: str):
        video = self.get_video_by_id(video_id)
        if video:
            video.status = status
            self.db.flush()
        return video
    
    def update_video(self, video_id: int, **kwargs):
        video = self.get_video_by_id(video_id)
        if video:
            for key, value in kwargs.items():
                setattr(video, key, value)
            self.db.flush()
        return video
    
    def save_fragments(self, video_id: int, fragments: list):
        video = self.get_video_by_id(video_id)
        if not video:
            logger.error(f"Video {video_id} not found")
            return
        saved = []
        for frag in fragments:
            db_frag = Fragment(
                video_id=video_id,
                timecode_start=frag.start_time,
                timecode_end=frag.end_time,
                s3_url=frag.s3_url,
                text=frag.text,
                tags=frag.tags,
                speech_confidence=frag.speech_confidence,
                no_speech_prob=frag.no_speech_prob,
                language=frag.language
            )
            self.db.add(db_frag)
            saved.append(db_frag)
            logger.info(f"Фрагмент {db_frag.id}({db_frag.timecode_start} - {db_frag.timecode_end}) сохранен")
        self.db.flush()
        for frag in saved:
            try:
                add_new_fragment(frag)
            except Exception as e:
                logger.error(f"Error indexing fragment {frag.id}: {e}")
        return saved
    
    def get_all_videos_with_fragments_count(self):
        videos = self.db.execute(select(Video)).scalars().all()
        result = []
        for video in videos:
            count = self.db.execute(select(func.count()).select_from(Fragment).where(Fragment.video_id == video.id)).scalar()
            result.append({"id": video.id, "name": video.name, "status": video.status, "fragments_count": count})
        return result
    
    def get_video_fragments(self, video_id: int):
        return self.db.execute(select(Fragment).where(Fragment.video_id == video_id).order_by(Fragment.timecode_start)).scalars().all()
    
    def get_fragment_by_id(self, fragment_id: int):
        return self.db.query(Fragment).filter(Fragment.id == fragment_id).first()
    
    def delete_video(self, video_id: int):
        self.db.execute(delete(Fragment).where(Fragment.video_id == video_id))
        self.db.execute(delete(Video).where(Video.id == video_id))
        self.db.flush()
