from embed import embed_query, MODEL
from cache import make_key, get_vector, set_vector


async def search(connection, query, year=None, runtime=None, min_rating=None):

    key = make_key(MODEL, query)
    vec = get_vector(key)
    if vec is None:
        vec = await embed_query(query)
        set_vector(key, vec)

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



