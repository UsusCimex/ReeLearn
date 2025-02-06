from db.models.fragment import Fragment
from utils.elasticsearch_utils import get_elasticsearch
from core.config import settings
from sqlalchemy import select
from core.logger import logger
from core.exceptions import DatabaseError, ElasticsearchException
from utils.video_processing import SmartVideoFragmenter

def search_in_elasticsearch(query, exact=False, tags=None, min_score=1.0):
    index_name = settings.ELASTICSEARCH_INDEX_NAME
    try:
        # Определяем язык запроса с помощью статического метода
        detected_lang = SmartVideoFragmenter.detect_language(query)
        if detected_lang == "ru":
            fields = ["text.ru_fuzzy^3", "text.ngram^2", "text"]
        else:
            fields = ["text.en_fuzzy^3", "text.ngram^2", "text"]

        logger.info(f"Incoming query: '{query}'; Detected language: {detected_lang}; Searching in fields: {fields}")

        if exact:
            query_clause = {
                "match_phrase": {
                    fields[2]: {
                        "query": query,
                        "slop": 0
                    }
                }
            }
        else:
            query_clause = {
                "multi_match": {
                    "query": query,
                    "fields": fields,
                    "operator": "and",
                    "fuzziness": "AUTO"
                }
            }

        if tags:
            tag_clause = {"terms": {"tags": tags}}
        else:
            tag_clause = None

        bool_query = {"must": [query_clause]}
        if tag_clause:
            bool_query["must"].append(tag_clause)

        search_body = {
            "query": {
                "bool": bool_query
            },
            "min_score": min_score,
            "size": 100
        }

        es = get_elasticsearch()
        res = es.search(index=index_name, body=search_body)
        return res["hits"]["hits"]
    except Exception as e:
        logger.error(f"Error in search_in_elasticsearch: {e}", exc_info=True)
        raise e

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
            videos[vid]["fragments"].append({
                "fragment_id": frag_id,
                "text": frag.text,
                "timecode_start": frag.timecode_start,
                "timecode_end": frag.timecode_end,
                "score": hit["_score"],
                "s3_url": frag.s3_url
            })
    results = list(videos.values())
    results.sort(key=lambda x: max(f["score"] for f in x["fragments"]), reverse=True)
    return results
