from typing import List
from fastapi import APIRouter, HTTPException
from db.base import Session
from db.repositories.video_repository import VideoRepository
from schemas.video import VideoFragmentsResponse, FragmentInfo, VideoInfo
from utils.s3_utils import generate_presigned_url
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=List[VideoInfo])
def get_videos():
    """
    Получить список всех видео.
    """
    try:
        with Session() as session:
            # Получаем все видео
            video_repo = VideoRepository(session)
            videos_data = video_repo.get_all_videos_with_fragments_count()
            
            result = [
                VideoInfo(
                    id=video["id"],
                    name=video["name"],
                    status=video["status"],
                    fragments_count=video["fragments_count"]
                )
                for video in videos_data
            ]
            
            return result
    except Exception as e:
        logger.error(f"Error fetching videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching videos: {str(e)}")

@router.get("/{video_id}/fragments", response_model=VideoFragmentsResponse)
def get_video_fragments(
    video_id: int
):
    """
    Получить все фрагменты видео с их субтитрами.
    """
    try:
        with Session() as session:
            # Проверяем существование видео
            video_repo = VideoRepository(session)
            video = video_repo.get_video_by_id(video_id)
            
            if not video:
                raise HTTPException(status_code=404, detail="Видео не найдено")
            
            # Получаем все фрагменты видео
            fragments = video_repo.get_video_fragments(video_id)
            
            # Преобразуем фрагменты в response модель
            fragments_info = [
                FragmentInfo(
                    id=fragment.id,
                    timecode_start=fragment.timecode_start,
                    timecode_end=fragment.timecode_end,
                    text=fragment.text,
                    s3_url=generate_presigned_url(fragment.s3_url),
                    tags=fragment.tags or []
                )
                for fragment in fragments
            ]
            
            return VideoFragmentsResponse(
                video_id=video_id,
                fragments=fragments_info
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fragments for video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching video fragments: {str(e)}")
