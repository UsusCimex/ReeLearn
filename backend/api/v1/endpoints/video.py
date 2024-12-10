from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.dependencies import get_db
from db.models.videos import Video
from db.models.fragments import Fragment
from schemas.video import VideoFragmentsResponse, FragmentInfo, VideoListResponse, VideoInfo
from utils.s3_utils import generate_presigned_url
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=List[VideoInfo])
async def get_videos(
    session: AsyncSession = Depends(get_db)
):
    """
    Получить список всех видео.
    """
    try:
        # Получаем все видео
        videos = await session.execute(
            select(Video)
        )
        videos = videos.scalars().all()
        
        result = []
        for video in videos:
            try:
                # Получаем количество фрагментов для видео
                fragments_count = await session.execute(
                    select(Fragment)
                    .where(Fragment.video_id == video.id)
                )
                fragments_count = len(fragments_count.scalars().all())
                
                result.append(VideoInfo(
                    id=video.id,
                    name=video.name,
                    status=video.status,
                    fragments_count=fragments_count
                ))
            except Exception as e:
                logger.error(f"Error processing video {video.id}: {str(e)}")
                # Пропускаем видео с ошибкой, но продолжаем обработку остальных
                continue
        
        return result
    except Exception as e:
        logger.error(f"Error fetching videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching videos: {str(e)}")

@router.get("/{video_id}/fragments", response_model=VideoFragmentsResponse)
async def get_video_fragments(
    video_id: int,
    session: AsyncSession = Depends(get_db)
):
    """
    Получить все фрагменты видео с их субтитрами.
    """
    try:
        # Проверяем существование видео
        video = await session.execute(
            select(Video).where(Video.id == video_id)
        )
        video = video.scalar_one_or_none()
        if not video:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        
        # Получаем все фрагменты видео
        fragments = await session.execute(
            select(Fragment)
            .where(Fragment.video_id == video_id)
            .order_by(Fragment.timecode_start)
        )
        fragments = fragments.scalars().all()
        
        # Преобразуем фрагменты в response модель
        fragments_info = []
        for fragment in fragments:
            presigned_url = await generate_presigned_url(fragment.s3_url)
            fragments_info.append(
                FragmentInfo(
                    id=fragment.id,
                    timecode_start=fragment.timecode_start,
                    timecode_end=fragment.timecode_end,
                    text=fragment.text,
                    s3_url=presigned_url,  # Use presigned URL instead of direct S3 URL
                    tags=fragment.tags or []
                )
            )
        
        return VideoFragmentsResponse(
            video_id=video_id,
            fragments=fragments_info
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fragments for video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching video fragments: {str(e)}")
