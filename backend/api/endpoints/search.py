from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from db.repositories.video_repository import VideoRepository
from schemas.search import SearchResultResponse, SearchResult, SearchFragment, VideoInfo, SearchStatus
from utils.elasticsearch_utils import get_elasticsearch
from utils.s3_utils import generate_presigned_url
from db.base import SessionLocal
from core.config import settings
from core.logger import logger
from services.search_service import search_in_elasticsearch 
import random

router = APIRouter()

@router.get("", response_model=SearchResultResponse)
def search_videos(
    query: str, 
    exact: bool = False, 
    tags: Optional[List[str]] = Query(None), 
    max_fragments_per_video: int = 3,
    max_videos: int = 5
):
    try:
        # Выполнение поиска в Elasticsearch
        hits = search_in_elasticsearch(query, exact, tags)
        fragment_ids = [hit["_source"]["fragment_id"] for hit in hits]
        scores = {hit["_source"]["fragment_id"]: hit["_score"] for hit in hits}
        
        # Открытие сессии базы данных
        db = SessionLocal()
        repo = VideoRepository(db)
        video_fragments = {}
        
        # Получение фрагментов и видео
        for frag_id in fragment_ids:
            frag = repo.get_fragment_by_id(frag_id)
            if frag:
                video = repo.get_video_by_id(frag.video_id)
                if video:
                    if video.id not in video_fragments:
                        video_fragments[video.id] = {
                            "video": VideoInfo(
                                video_id=str(video.id),
                                name=video.name,
                                description=video.description,
                                s3_url=generate_presigned_url(video.s3_url, expiration=3600)
                            ),
                            "fragments": []
                        }
                    frag_url = generate_presigned_url(frag.s3_url, expiration=3600)
                    video_fragments[video.id]["fragments"].append({
                        "fragment_id": str(frag.id),
                        "text": frag.text,
                        "timecode_start": frag.timecode_start,
                        "timecode_end": frag.timecode_end,
                        "s3_url": frag_url,
                        "score": scores[frag.id]
                    })
        
        # Ограничиваем количество фрагментов и видео
        results = []
        for vid, data in video_fragments.items():
            data["fragments"].sort(key=lambda x: x["score"], reverse=True)
            # Ограничиваем количество фрагментов для каждого видео
            data["fragments"] = data["fragments"][:max_fragments_per_video]
            results.append(SearchResult(
                video=data["video"],
                fragments=[SearchFragment(**f) for f in data["fragments"]],
                fragments_count=len(data["fragments"])
            ))

        # Ограничиваем количество видео
        results = random.sample(results, k=min(max_videos, len(results)))

        # Сортировка результатов по максимальному score
        results.sort(key=lambda x: max(f.score for f in x.fragments) if x.fragments else 0, reverse=True)

        db.close()
        return SearchResultResponse(status=SearchStatus.completed, results=results)

    except Exception as e:
        logger.error(str(e))
        return SearchResultResponse(status=SearchStatus.failed, results=[], error=str(e))