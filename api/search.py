import redis
import hashlib
from redis.exceptions import RedisError
import asyncpg
from pgvector.asyncpg import register_vector
from embed import embed_query
import json


red = redis.Redis(host="localhost", port=6379, decode_responses=True)
connection = asyncpg.connect("postgresql://localhost/moviedb")



async def search(connection, query, year=None, runtime=None, min_rating=None):
    try:
        clean = query.lower().strip()
        hashed_key = hashlib.sha256(clean.encode("utf-8")).hexdigest()
        cached_query = red.get(hashed_key)
        if cached_query:
            #From Cache
            vec = json.loads(cached_query)
        else:
            #From API - Not Cached
            vec = await embed_query(clean)
            red.set(hashed_key, json.dumps(vec), ex=60*60*24*30) #30 Days
    except RedisError as e:
        print(f"error caught: {e}. Moving on...")
        vec = await embed_query(clean)

    #Order by cosine distance between query vector and stored embeddings
    sql_query = '''SELECT id, title, year, genres, vote_average, overview, embedding <=> $1 AS distance, 
    1 - (embedding <=> $1) AS similarity
    FROM movies 
    WHERE (year >= $2::int OR $2::int IS NULL) 
    AND (runtime <= $3::int OR $3::int IS NULL) 
    AND (vote_average >= $4::real OR $4::real IS NULL)
    ORDER BY distance ASC 
    LIMIT 12;'''

    rows = await connection.fetch(sql_query, vec, year, runtime, min_rating)

    return [
        {**dict(r), "similarity": round(r["similarity"], 4)}
        for r in rows
    ]



