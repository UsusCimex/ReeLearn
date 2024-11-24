from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.dependencies import get_db
from db.models.videos import Video
from db.models.fragments import Fragment
from schemas.video import VideoFragmentsResponse, FragmentInfo

router = APIRouter()

@router.get("/videos/{video_id}/fragments", response_model=VideoFragmentsResponse)
async def get_video_fragments(
    video_id: int,
    session: AsyncSession = Depends(get_db)
):
    """
    Получить все фрагменты видео с их субтитрами.
    """
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
    fragments_info = [
        FragmentInfo(
            id=fragment.id,
            timecode_start=fragment.timecode_start,
            timecode_end=fragment.timecode_end,
            text=fragment.text,
            s3_url=fragment.s3_url,
            tags=fragment.tags or []
        )
        for fragment in fragments
    ]
    
    return VideoFragmentsResponse(
        video_id=video_id,
        fragments=fragments_info
    )
