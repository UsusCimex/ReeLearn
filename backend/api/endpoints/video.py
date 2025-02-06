from typing import List
from fastapi import APIRouter, HTTPException
from db.base import SessionLocal
from db.repositories.video_repository import VideoRepository
from schemas.video import VideoFragmentsResponse, FragmentInfo, VideoInfo
from utils.s3_utils import generate_presigned_url, delete_file_from_s3
from utils.elasticsearch_utils import delete_fragment_by_id
from core.logger import logger

router = APIRouter()

@router.get("", response_model=List[VideoInfo])
def get_videos():
    try:
        db = SessionLocal()
        repo = VideoRepository(db)
        videos = repo.get_all_videos_with_fragments_count()
        db.close()
        return [VideoInfo(id=video["id"], name=video["name"], status=video["status"], fragments_count=video["fragments_count"]) for video in videos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}/fragments", response_model=VideoFragmentsResponse)
def get_video_fragments(video_id: int):
    try:
        with SessionLocal() as session:
            video_repo = VideoRepository(session)
            video = video_repo.get_video_by_id(video_id)
            if not video:
                raise HTTPException(status_code=404, detail="Видео не найдено")
            
            fragments = video_repo.get_video_fragments(video_id)
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
            
            video_url = generate_presigned_url(video.s3_url) if video.s3_url else ""
            
            return VideoFragmentsResponse(
                video_id=video_id,
                video_url=video_url,
                fragments=fragments_info
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fragments for video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching video fragments: {str(e)}")


@router.delete("/{video_id}")
def delete_video(video_id: int):
    try:
        db = SessionLocal()
        repo = VideoRepository(db)
        video = repo.get_video_by_id(video_id)
        if not video:
            db.close()
            raise HTTPException(status_code=404, detail="Video not found")
        fragments = repo.get_video_fragments(video_id)
        for frag in fragments:
            try:
                delete_fragment_by_id(frag.id)
            except:
                pass
            try:
                delete_file_from_s3(frag.s3_url)
            except:
                pass
        if video.s3_url:
            try:
                delete_file_from_s3(video.s3_url)
            except:
                pass
        repo.delete_video(video_id)
        db.commit()
        db.close()
        return {"message": "Video deleted", "video_id": video_id}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
