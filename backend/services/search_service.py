from db.models.fragment import Fragment
from utils.elasticsearch_utils import get_elasticsearch
from core.config import settings
from sqlalchemy import select
from core.logger import logger
from core.exceptions import DatabaseError, ElasticsearchException

def search_in_elasticsearch(query, exact=False, tags=None, min_score=1.0):
    es = get_elasticsearch()
    must = []
    if query:
        if exact:
            must.append({"match_phrase": {"text": {"query": query, "slop": 0}}})
        else:
            must.append({"multi_match": {"query": query, "fields": ["text", "text.keyword"], "operator": "or", "fuzziness": "AUTO"}})
            must.append({"match_phrase": {"text": {"query": query, "slop": 2, "boost": 2.0}}})
    if tags:
        must.append({"terms": {"tags": tags}})
    body = {"query": {"bool": {"should": must, "minimum_should_match": 1}}, "min_score": min_score, "size": 100}
    try:
        res = es.search(index=settings.ELASTICSEARCH_INDEX_NAME, body=body)
        return res["hits"]["hits"]
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise ElasticsearchException(str(e))
def get_fragments_with_videos(db, fragment_ids):
    fragments = db.execute(select(Fragment).where(Fragment.id.in_(fragment_ids))).scalars().all()
    return fragments
def assemble_search_results(hits, fragments, results_per_video=2):
    frag_dict = {str(f.id): f for f in fragments}
    videos = {}
    for hit in hits:
        frag_id = str(hit["_source"]["fragment_id"])
        frag = frag_dict.get(frag_id)
        if not frag or not frag.video:
            continue
        vid = str(frag.video.id)
        if vid not in videos:
            videos[vid] = {"video_id": vid, "video_name": frag.video.name, "fragments": []}
        if len(videos[vid]["fragments"]) < results_per_video:
            videos[vid]["fragments"].append({"fragment_id": frag_id, "text": frag.text, "timecode_start": frag.timecode_start, "timecode_end": frag.timecode_end, "score": hit["_score"], "s3_url": frag.s3_url})
    results = list(videos.values())
    results.sort(key=lambda x: max(f["score"] for f in x["fragments"]), reverse=True)
    return results
