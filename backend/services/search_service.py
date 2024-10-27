from utils.elasticsearch_utils import es
from core.config import settings
from sqlalchemy.orm import Session
from models import Fragment
from database import SessionLocal
from utils.s3_utils import generate_presigned_url

def search_in_elasticsearch(query, exact=False, tags=None):
    index_name = settings.ELASTICSEARCH_INDEX_NAME

    must_queries = []
    
    if query:
        if exact:
            must_queries.append({
                "match_phrase": {
                    "text": {
                        "query": query,
                        "slop": 0
                    }
                }
            })
        else:
            must_queries.append({
                "match": {
                    "text": {
                        "query": query,
                        "operator": "and",
                        "fuzziness": "AUTO",
                        "max_expansions": 50
                    }
                }
            })

    if tags:
        must_queries.append({
            "terms": {
                "tags": tags
            }
        })

    search_body = {
        "query": {
            "bool": {
                "must": must_queries
            }
        }
    }

    res = es.search(index=index_name, body=search_body)
    hits = res['hits']['hits']
    return hits

def get_fragments_from_db(fragment_ids):
    db = SessionLocal()
    try:
        fragments = db.query(Fragment).filter(Fragment.id.in_(fragment_ids)).all()
        return fragments
    finally:
        db.close()

def assemble_search_results(hits, fragments):
    # Создаем словарь для быстрого доступа к данным из Elasticsearch по ID
    id_to_source = {int(hit['_id']): hit['_source'] for hit in hits}
    
    results = []
    for fragment in fragments:
        video = fragment.video
        source = id_to_source.get(fragment.id, {})
        fragment_text = source.get('text', "")
        fragment_tags = source.get('tags', [])

        try:
            presigned_url = generate_presigned_url(fragment.s3_url)
        except Exception as e:
            presigned_url = fragment.s3_url

        result = {
            'presigned_url': presigned_url,
            'video_name': video.name,
            'video_description': video.description,
            'timecode_start': fragment.timecode_start,
            'timecode_end': fragment.timecode_end,
            'text': fragment_text,
            'tags': fragment_tags
        }
        results.append(result)
    return results
