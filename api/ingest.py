import json
import pickle
from pathlib import Path
import asyncpg
from pgvector.asyncpg import register_vector
import asyncio

import pandas as pd

from embed import embed_batch, BATCH

DATA = Path(__file__).parent.parent / "dataset" / "movie.csv"
CLEAN = Path("movie_clean.pkl")
CKPT = Path("embeddings.pkl")

def names(cell):
    try:
        return [d["name"] for d in json.loads(cell)]
    except (TypeError, json.JSONDecodeError):
        return []

def embed_text(r):
    genres = ", ".join(r["genre_list"])
    return f"{r['title']} ({r['year']}). Genres: {genres}. {r['overview']}"

def load_clean():
    if CLEAN.exists():
        return pd.read_pickle(CLEAN)
    df = pd.read_csv(DATA)
    df["genre_list"] = df["genres"].apply(names)
    df = df[df["overview"].notna() & (df["overview"].str.len() > 40)]
    df["year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year
    df["embed_text"] = df.apply(embed_text, axis=1)
    df = df.reset_index(drop=True)
    df.to_pickle(CLEAN)
    return df

df = load_clean()
print(f"{len(df)} movies")
print(df["embed_text"].iloc[0])

texts = df["embed_text"].tolist()
vectors = pickle.loads(CKPT.read_bytes()) if CKPT.exists() else []
print(f"resuming at {len(vectors)}/{len(texts)}")

for start in range(len(vectors), len(texts), BATCH):
        chunk = texts[start:start + BATCH]
        vectors.extend(embed_batch(chunk))
        CKPT.write_bytes(pickle.dumps(vectors))
        print(f"{len(vectors)}/{len(texts)}")

assert len(vectors) == len(df), f"{len(vectors)} vectors vs {len(df)} rows"
df["embedding"] = vectors

INSERT_SQL = """
INSERT INTO movies (id, title, overview, genres, year, runtime,
                    vote_average, vote_count, embed_text, embedding)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
ON CONFLICT (id) DO UPDATE SET
    title       = EXCLUDED.title,
    overview    = EXCLUDED.overview,
    genres      = EXCLUDED.genres,
    year        = EXCLUDED.year,
    runtime     = EXCLUDED.runtime,
    vote_average= EXCLUDED.vote_average,
    vote_count  = EXCLUDED.vote_count,
    embed_text  = EXCLUDED.embed_text,
    embedding   = EXCLUDED.embedding
"""

def to_int(v):
     """native int or None"""
     return None if pd.isna(v) else int(v)

async def insert(df):
    #Establish Connection
    conn = await asyncpg.connect("postgresql://localhost/moviedb")
    #Register Vector
    await register_vector(conn)
    #Batch insert with an upsert on conflict
    try:
          rows = [
               (
                    int(r.id),
                    r.title,
                    r.overview,
                    r.genre_list,
                    to_int(r.year),
                    to_int(r.runtime),
                    float(r.vote_average),
                    to_int(r.vote_count),
                    r.embed_text,
                    r.embedding,
               )
               for r in df.itertuples()
          ]
          await conn.executemany(INSERT_SQL, rows)
          count = await conn.fetchval("SELECT COUNT(*) FROM movies")
          print(f"inserted, table now has {count} rows")
    finally:
        await conn.close()
asyncio.run(insert(df))
print("done!")




