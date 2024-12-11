from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from db.repositories.video_repository import VideoRepository
from schemas.search import SearchResultResponse, SearchResult, SearchStatus, SearchFragment, VideoInfo
from utils.elasticsearch_utils import get_elasticsearch
from utils.s3_utils import generate_presigned_url
from db.base import Session
from core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=SearchResultResponse)
def search_videos_endpoint(
    query: str,
    exact: bool = False,
    tags: Optional[List[str]] = Query(default=None)
) -> SearchResultResponse:
    """
    Синхронный поиск видео по запросу.
    
    Args:
        query: Поисковый запрос
        exact: Точное совпадение или нет
        tags: Список тегов для фильтрации
    """
    try:
        # Создаем клиент Elasticsearch
        es = get_elasticsearch()
        
        # Формируем поисковый запрос
        search_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match" if not exact else "match_phrase": {
                                "text": query
                            }
                        }
                    ]
                }
            }
        }
        
        # Добавляем фильтр по тегам если они указаны
        if tags:
            search_query["query"]["bool"]["filter"] = [
                {"terms": {"tags": tags}}
            ]
        
        # Выполняем поиск
        response = es.search(
            index=settings.ELASTICSEARCH_INDEX_NAME,
            body=search_query,
            size=100
        )
        
        # Получаем ID фрагментов из результатов
        hits = response["hits"]["hits"]
        fragment_ids = [hit["_source"]["fragment_id"] for hit in hits]
        
        # Создаем словарь для хранения score каждого фрагмента
        fragment_scores = {hit["_source"]["fragment_id"]: hit["_score"] for hit in hits}
        
        # Получаем полную информацию о фрагментах из базы данных
        with Session() as session:
            repo = VideoRepository(session)
            results = []
            video_fragments = {}  # Dictionary to group fragments by video
            
            for fragment_id in fragment_ids:
                fragment = repo.get_fragment_by_id(fragment_id)
                if fragment:
                    video = repo.get_video_by_id(fragment.video_id)
                    if video:
                        if video.id not in video_fragments:
                            video_fragments[video.id] = {
                                'video': VideoInfo(
                                    video_id=str(video.id),
                                    name=video.name,
                                    description=video.description,
                                    s3_url=generate_presigned_url(video.s3_url, expiration=3600)  # Генерируем presigned URL из ключа S3
                                ),
                                'fragments': []
                            }
                        
                        # Генерируем публичный URL для фрагмента
                        fragment_url = generate_presigned_url(fragment.s3_url, expiration=3600)  # URL с временем жизни 1 час
                        
                        video_fragments[video.id]['fragments'].append({
                            'fragment_id': str(fragment.id),
                            'text': fragment.text,
                            'timecode_start': fragment.timecode_start,
                            'timecode_end': fragment.timecode_end,
                            's3_url': fragment_url,
                            'score': fragment_scores[fragment.id]
                        })
            
            # Sort results by best fragment score
            for video_id, video_data in video_fragments.items():
                # Sort fragments by score
                video_data['fragments'].sort(key=lambda x: x['score'], reverse=True)
                
                # Convert dictionary fragments to SearchFragment objects
                fragments = [
                    SearchFragment(
                        fragment_id=f['fragment_id'],
                        text=f['text'],
                        timecode_start=f['timecode_start'],
                        timecode_end=f['timecode_end'],
                        s3_url=f['s3_url'],
                        score=f['score']
                    ) for f in video_data['fragments']
                ]
                
                results.append(SearchResult(
                    video=video_data['video'],
                    fragments=fragments,
                    fragments_count=len(fragments)
                ))
            
            # Sort results by best fragment score
            results.sort(key=lambda x: max(f.score for f in x.fragments) if x.fragments else 0, reverse=True)
        
        return SearchResultResponse(
            status=SearchStatus.COMPLETED,
            results=results,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return SearchResultResponse(
            status=SearchStatus.FAILED,
            results=[],
            error=str(e)
        )