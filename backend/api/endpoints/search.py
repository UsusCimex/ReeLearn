from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from db.repositories.video_repository import VideoRepository
from schemas.search import SearchResultResponse, SearchResult, SearchFragment, VideoInfo, SearchStatus
from utils.elasticsearch_utils import get_elasticsearch
from utils.s3_utils import generate_presigned_url
from db.base import SessionLocal
from core.config import settings
from core.logger import logger

router = APIRouter()

@router.get("", response_model=SearchResultResponse)
def search_videos(query: str, exact: bool = False, tags: Optional[List[str]] = Query(None)):
    try:
        es = get_elasticsearch()
        body = {"query": {"bool": {"must": [{"match_phrase" if exact else "match": {"text": query}}]}}, "size": 100}
        if tags:
            body["query"]["bool"]["filter"] = [{"terms": {"tags": tags}}]
        response = es.search(index=settings.ELASTICSEARCH_INDEX_NAME, body=body)
        hits = response["hits"]["hits"]
        fragment_ids = [hit["_source"]["fragment_id"] for hit in hits]
        scores = {hit["_source"]["fragment_id"]: hit["_score"] for hit in hits}
        db = SessionLocal()
        repo = VideoRepository(db)
        video_fragments = {}
        for frag_id in fragment_ids:
            frag = repo.get_fragment_by_id(frag_id)
            if frag:
                video = repo.get_video_by_id(frag.video_id)
                if video:
                    if video.id not in video_fragments:
                        video_fragments[video.id] = {"video": VideoInfo(video_id=str(video.id), name=video.name, description=video.description, s3_url=generate_presigned_url(video.s3_url, expiration=3600)), "fragments": []}
                    frag_url = generate_presigned_url(frag.s3_url, expiration=3600)
                    video_fragments[video.id]["fragments"].append({"fragment_id": str(frag.id), "text": frag.text, "timecode_start": frag.timecode_start, "timecode_end": frag.timecode_end, "s3_url": frag_url, "score": scores[frag.id]})
        results = []
        for vid, data in video_fragments.items():
            data["fragments"].sort(key=lambda x: x["score"], reverse=True)
            results.append(SearchResult(video=data["video"], fragments=[SearchFragment(**f) for f in data["fragments"]], fragments_count=len(data["fragments"])))
        results.sort(key=lambda x: max(f.score for f in x.fragments) if x.fragments else 0, reverse=True)
        db.close()
        return SearchResultResponse(status=SearchStatus.completed, results=results)
    except Exception as e:
        logger.error(str(e))
        return SearchResultResponse(status=SearchStatus.failed, results=[], error=str(e))
